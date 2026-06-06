from __future__ import annotations

from fastapi.testclient import TestClient

from raceweek.main import app

client = TestClient(app)


def test_real_data_default_has_empty_fantasy_domains_without_demo_fallback() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})

    mode = client.get("/api/v1/data-mode").json()
    assert mode["mode"] == "real"

    market = client.get("/api/v1/fantasy/market").json()
    team = client.get("/api/v1/fantasy/team/current").json()
    freshness = client.get("/api/v1/data-freshness").json()["items"]

    assert market["items"] == []
    assert market["freshness"]["status"] == "missing"
    assert market["freshness"]["isBlocking"] is True
    assert team["items"] == []
    assert team["freshness"]["status"] == "missing"
    assert {item["key"] for item in freshness} >= {
        "race.calendar",
        "race.current_meeting",
        "race.sessions",
        "race.weather",
        "race.race_control",
        "fantasy.market",
        "fantasy.user_team",
        "fantasy.scores",
        "fantasy.league",
        "ai.provider",
    }


def test_optimizer_blocks_real_data_mode_until_market_and_team_are_ready() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})

    response = client.post(
        "/api/v1/optimizer/recommendations",
        json={
            "teamSnapshotId": "team_demo_01",
            "eventId": "event_demo_01",
            "strategyMode": "balanced",
            "maxOptions": 1,
        },
    )

    assert response.status_code == 409
    detail = response.json()["detail"]
    assert detail["code"] == "optimizer_readiness_blocked"
    assert [blocker["key"] for blocker in detail["blockers"]] == [
        "fantasy.market",
        "fantasy.user_team",
    ]
    assert all("demo" not in blocker["message"].lower() for blocker in detail["blockers"])


def test_optimizer_readiness_reports_exact_missing_data_blockers() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})

    readiness = client.get("/api/v1/readiness/optimizer").json()

    assert readiness["ready"] is False
    assert readiness["canRunWithWarnings"] is False
    assert {item["key"] for item in readiness["blockingReasons"]} >= {
        "fantasy.market",
        "fantasy.user_team",
    }
    assert readiness["warnings"][0]["key"] == "race.current_meeting"


def test_optimizer_readiness_is_ready_after_market_and_team_selection() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    client.post("/api/v1/fantasy/import/market", json=_structured_market())
    asset_ids = [asset["assetId"] for asset in _structured_market()["assets"]]
    client.post(
        "/api/v1/onboarding/teams/select",
        json={
            "eventId": "event_2026_08",
            "teams": [
                {
                    "slot": slot,
                    "teamName": f"Ready Slot {slot}",
                    "costCapMillions": 100,
                    "freeTransfers": 2,
                    "assetIds": asset_ids,
                }
                for slot in [1, 2, 3]
            ],
        },
    )

    readiness = client.get("/api/v1/readiness/optimizer").json()

    assert readiness["ready"] is True
    assert readiness["blockingReasons"] == []
    assert readiness["canRunWithWarnings"] is True


def test_onboarding_mode_choice_persists_demo_or_real_without_real_fallback() -> None:
    demo = client.post("/api/v1/onboarding/mode", json={"mode": "demo"}).json()
    assert demo == {"mode": "demo", "allowDemoFallback": True}
    assert client.get("/api/v1/onboarding/status").json()["nextRoute"] == "/dashboard"

    real = client.post("/api/v1/onboarding/mode", json={"mode": "real"}).json()
    assert real == {"mode": "real", "allowDemoFallback": False}
    status = client.get("/api/v1/onboarding/status").json()
    assert status["mode"] == "real"
    assert status["nextRoute"] == "/onboarding"


def test_market_import_preview_confirm_persists_real_rows_and_updates_freshness() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    raw_text = "\n".join(
        [
            "season,round,asset_kind,asset_name,team_name,price_m,points,selection",
            "2026,8,driver,Example Driver,Example Racing,12.3,44,12.5%",
            "2026,8,constructor,Example Constructor,,22.4,68,0.32",
        ]
    )

    preview = client.post(
        "/api/v1/imports/preview",
        json={
            "templateType": "market_prices",
            "contentType": "text/csv",
            "rawText": raw_text,
        },
    ).json()

    assert preview["importable"] is True
    assert preview["inferredDelimiter"] == ","
    assert preview["mappedHeaders"]["asset_kind"] == "asset_kind"
    assert preview["rows"][0]["assetType"] == "driver"
    assert preview["rows"][0]["displayName"] == "Example Driver"
    assert preview["rows"][1]["ownershipPct"] == 32.0

    confirmed = client.post(
        "/api/v1/imports/confirm",
        json={
            "templateType": "market_prices",
            "contentType": "text/csv",
            "rawText": raw_text,
            "contentHash": preview["contentHash"],
        },
    ).json()

    assert confirmed["status"] == "imported"
    assert confirmed["itemCount"] == 2

    market = client.get("/api/v1/fantasy/market").json()
    assert {item["displayName"] for item in market["items"]} == {
        "Example Constructor",
        "Example Driver",
    }
    assert all(not item["sourceSnapshotId"].startswith("snapshot_demo") for item in market["items"])
    assert market["freshness"]["status"] == "real_current"
    assert market["freshness"]["recordCount"] == 2


def test_structured_market_import_exposes_onboarding_catalog_metadata() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    response = client.post("/api/v1/fantasy/import/market", json=_structured_market())

    assert response.status_code == 201

    market = client.get("/api/v1/fantasy/market").json()
    driver_one = next(item for item in market["items"] if item["assetId"] == "real_driver_one")
    driver_two = next(item for item in market["items"] if item["assetId"] == "real_driver_two")
    constructor = next(
        item for item in market["items"] if item["assetId"] == "real_constructor_one"
    )

    assert driver_one["shortName"] == "DTO"
    assert driver_one["teamColor"] == "#0066CC"
    assert driver_two["shortName"] == "TWO"
    assert driver_two["teamColor"].startswith("#")
    assert constructor["teamColor"] == "#0066CC"
    assert market["freshness"]["status"] == "real_current"


def test_onboarding_team_selection_uses_loaded_market_assets_for_three_slots() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    client.post("/api/v1/fantasy/import/market", json=_structured_market())
    asset_ids = [asset["assetId"] for asset in _structured_market()["assets"]]

    response = client.post(
        "/api/v1/onboarding/teams/select",
        json={
            "eventId": "event_2026_08",
            "teams": [
                {
                    "slot": 1,
                    "teamName": "Real Slot One",
                    "costCapMillions": 100,
                    "freeTransfers": 2,
                    "assetIds": asset_ids,
                },
                {
                    "slot": 2,
                    "teamName": "Real Slot Two",
                    "costCapMillions": 100,
                    "freeTransfers": 1,
                    "assetIds": asset_ids,
                },
                {
                    "slot": 3,
                    "teamName": "Real Slot Three",
                    "costCapMillions": 100,
                    "freeTransfers": 0,
                    "assetIds": asset_ids,
                },
            ],
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert [team["slot"] for team in body["items"]] == [1, 2, 3]
    assert body["items"][0]["budgetUsedMillions"] == 96
    assert body["items"][0]["budgetRemainingMillions"] == 4
    assert body["freshness"]["status"] == "real_current"

    current = client.get("/api/v1/fantasy/team/current").json()
    assert [team["teamName"] for team in current["items"]] == [
        "Real Slot One",
        "Real Slot Two",
        "Real Slot Three",
    ]


def test_onboarding_team_selection_requires_real_market_catalog_first() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})

    response = client.post(
        "/api/v1/onboarding/teams/select",
        json={
            "eventId": "event_2026_08",
            "teams": [
                {
                    "slot": 1,
                    "teamName": "No Catalog",
                    "costCapMillions": 100,
                    "freeTransfers": 2,
                    "assetIds": [
                        "real_driver_one",
                        "real_driver_two",
                        "real_driver_three",
                        "real_driver_four",
                        "real_driver_five",
                        "real_constructor_one",
                        "real_constructor_two",
                    ],
                }
            ],
        },
    )

    assert response.status_code == 409
    assert "fantasy market" in response.json()["detail"]


def test_fantasy_readonly_status_explains_token_and_non_csv_paths() -> None:
    response = client.get("/api/v1/fantasy/read-only/status")

    assert response.status_code == 200
    body = response.json()
    assert body["source"] == "fantasy_readonly"
    assert body["canMutateFantasyAccount"] is False
    assert "FANTASY_SESSION_TOKEN" in body["requiredEnvVars"]
    assert body["structuredJsonImport"]["endpoint"] == "/api/v1/fantasy/import/market"
    assert body["csvFallback"]["endpoint"] == "/api/v1/imports/confirm"
    assert "secret" not in str(body).lower()


def test_import_preview_does_not_write_domain_rows_and_validation_is_row_specific() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    raw_text = "\n".join(
        [
            "season,round,asset_kind,asset_name,price_m",
            "2026,8,driver,Missing Price,",
        ]
    )

    preview = client.post(
        "/api/v1/imports/preview",
        json={
            "templateType": "market_prices",
            "contentType": "text/csv",
            "rawText": raw_text,
        },
    ).json()

    assert preview["importable"] is False
    assert preview["messages"][0]["rowNumber"] == 2
    assert preview["messages"][0]["column"] == "price_m"
    assert preview["messages"][0]["severity"] == "error"
    assert client.get("/api/v1/fantasy/market").json()["items"] == []


def test_team_state_and_slots_import_create_current_real_team() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    team_state = "\n".join(
        [
            "season,round,team_name,cost_cap_m,bank_m,free_transfers",
            "2026,8,Real Team,100,4.5,2",
        ]
    )
    team_slots = "\n".join(
        [
            "season,round,slot_type,slot_number,asset_name",
            "2026,8,driver,1,Driver One",
            "2026,8,driver,2,Driver Two",
            "2026,8,driver,3,Driver Three",
            "2026,8,driver,4,Driver Four",
            "2026,8,driver,5,Driver Five",
            "2026,8,constructor,1,Constructor One",
            "2026,8,constructor,2,Constructor Two",
        ]
    )

    for template_type, raw_text in [
        ("team_state", team_state),
        ("team_slots", team_slots),
    ]:
        preview = client.post(
            "/api/v1/imports/preview",
            json={
                "templateType": template_type,
                "contentType": "text/csv",
                "rawText": raw_text,
            },
        ).json()
        assert preview["importable"] is True
        client.post(
            "/api/v1/imports/confirm",
            json={
                "templateType": template_type,
                "contentType": "text/csv",
                "rawText": raw_text,
                "contentHash": preview["contentHash"],
            },
        )

    current = client.get("/api/v1/fantasy/team/current").json()

    assert current["freshness"]["status"] == "real_current"
    assert current["items"][0]["teamName"] == "Real Team"
    assert len(current["items"][0]["assets"]) == 7
    assert current["items"][0]["budgetRemainingMillions"] == 4.5


def test_correction_manual_import_templates_preview_confirm_and_apply_chips() -> None:
    client.post("/api/v1/data/reset", json={"scope": "all"})
    raw_templates = {
        "team_state": "\n".join(
            [
                "season,event_id,slot,team_name,cost_cap_millions,budget_used_millions,budget_remaining_millions,free_transfers,transfer_penalty_points,total_points,source_note",
                "2026,event_2026_08,1,Main Team,100,98.7,1.3,2,10,842,team screen",
            ]
        ),
        "chips_state": "\n".join(
            [
                "season,event_id,slot,chip_name,status,used_event_id,source_note",
                "2026,event_2026_08,1,wildcard,used,event_2026_03,used earlier",
            ]
        ),
        "team_slots": "\n".join(
            [
                "season,event_id,slot,asset_id,asset_type,display_name,constructor_name,boost_multiplier,source_note",
                "2026,event_2026_08,1,DRIVER_1,driver,Driver One,Example,1,slot",
                "2026,event_2026_08,1,DRIVER_2,driver,Driver Two,Example,1,slot",
                "2026,event_2026_08,1,DRIVER_3,driver,Driver Three,Example,1,slot",
                "2026,event_2026_08,1,DRIVER_4,driver,Driver Four,Example,1,slot",
                "2026,event_2026_08,1,DRIVER_5,driver,Driver Five,Example,1,slot",
                "2026,event_2026_08,1,TEAM_1,constructor,Constructor One,Example,1,slot",
                "2026,event_2026_08,1,TEAM_2,constructor,Constructor Two,Example,1,slot",
            ]
        ),
        "season_totals": "\n".join(
            [
                "season,event_id,slot,team_name,total_points,overall_rank,league_rank,source_note",
                "2026,event_2026_08,1,Main Team,842,123456,4,total",
            ]
        ),
        "transfer_history_optional": "\n".join(
            [
                "season,event_id,slot,transfer_number,out_asset_id,out_display_name,in_asset_id,in_display_name,penalty_points,chip_active,source_note",
                "2026,event_2026_08,1,1,OLD_DRIVER,Old Driver,DRIVER_1,Driver One,0,,history",
            ]
        ),
        "rival_team_slots": "\n".join(
            [
                "season,event_id,league_id,entry_name,rank,asset_id,asset_type,display_name,constructor_name,source_note",
                (
                    "2026,event_2026_08,league_1,Apex Hunters,1,DRIVER_1,"
                    "driver,Driver One,Example,rival"
                ),
            ]
        ),
    }

    listed_templates = {
        item["templateType"] for item in client.get("/api/v1/imports/templates").json()["items"]
    }
    assert set(raw_templates).issubset(listed_templates)

    for template_type, raw_text in raw_templates.items():
        preview = client.post(
            "/api/v1/imports/preview",
            json={
                "templateType": template_type,
                "contentType": "text/csv",
                "rawText": raw_text,
            },
        ).json()
        assert preview["importable"] is True, preview["messages"]
        confirmed = client.post(
            "/api/v1/imports/confirm",
            json={
                "templateType": template_type,
                "contentType": "text/csv",
                "rawText": raw_text,
                "contentHash": preview["contentHash"],
            },
        ).json()
        assert confirmed["itemCount"] == preview["rowCount"]

    team = client.get("/api/v1/fantasy/team/current").json()["items"][0]
    chips = {chip["chipName"]: chip for chip in team["chips"]}
    assert team["slot"] == 1
    assert team["budgetRemainingMillions"] == 1.3
    assert chips["wildcard"]["status"] == "used"
    assert chips["wildcard"]["usedEventId"] == "event_2026_03"


def _structured_market() -> dict[str, object]:
    return {
        "eventId": "event_2026_08",
        "sourceSnapshotId": "snapshot_manual_market_real_2026_08",
        "assets": [
            {
                "assetId": "real_driver_one",
                "assetType": "driver",
                "displayName": "Driver Test One",
                "shortName": "DTO",
                "constructorName": "Blue Racing",
                "teamColor": "#0066CC",
                "priceMillions": 20,
            },
            {
                "assetId": "real_driver_two",
                "assetType": "driver",
                "displayName": "Driver Test Two",
                "constructorName": "Green Racing",
                "priceMillions": 18,
            },
            {
                "assetId": "real_driver_three",
                "assetType": "driver",
                "displayName": "Driver Test Three",
                "constructorName": "Silver Racing",
                "priceMillions": 16,
            },
            {
                "assetId": "real_driver_four",
                "assetType": "driver",
                "displayName": "Driver Test Four",
                "constructorName": "Red Racing",
                "priceMillions": 12,
            },
            {
                "assetId": "real_driver_five",
                "assetType": "driver",
                "displayName": "Driver Test Five",
                "constructorName": "Yellow Racing",
                "priceMillions": 8,
            },
            {
                "assetId": "real_constructor_one",
                "assetType": "constructor",
                "displayName": "Blue Racing",
                "shortName": "BLU",
                "constructorName": "Blue Racing",
                "teamColor": "#0066CC",
                "priceMillions": 15,
            },
            {
                "assetId": "real_constructor_two",
                "assetType": "constructor",
                "displayName": "Green Racing",
                "constructorName": "Green Racing",
                "priceMillions": 7,
            },
        ],
    }
