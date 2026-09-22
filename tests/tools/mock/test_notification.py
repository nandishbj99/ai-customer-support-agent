import pytest
from app.seeds.seed_data import det_uuid
from app.tools.mock.notification import MockNotificationService


@pytest.mark.asyncio
async def test_send_notification_success():
    service = MockNotificationService()
    res = await service.send_notification(
        user_id=str(det_uuid(1)),
        channel="sms",
        message="Your refund of ₹500 has been processed.",
    )
    assert res.success is True
    assert res.data["channel"] == "sms"
    assert res.data["status"] == "delivered_mock"
    assert "notification_id" in res.data


@pytest.mark.asyncio
async def test_send_notification_invalid_channel():
    service = MockNotificationService()
    res = await service.send_notification(
        user_id=str(det_uuid(1)),
        channel="pigeon_post",
        message="Hello",
    )
    assert res.success is False
    assert res.error.code == "INVALID_CHANNEL"


@pytest.mark.asyncio
async def test_send_notification_invalid_user():
    service = MockNotificationService()
    res = await service.send_notification(
        user_id="",
        channel="sms",
        message="Hello",
    )
    assert res.success is False
    assert res.error.code == "INVALID_USER_ID"
