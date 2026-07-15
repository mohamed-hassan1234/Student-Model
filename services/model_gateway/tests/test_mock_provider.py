from devmind_model_gateway.providers import MockModelProvider, ProviderRequest


async def test_mock_provider_is_deterministic() -> None:
    provider = MockModelProvider()

    first = await provider.generate(ProviderRequest(prompt="  hello   DevMind  "))
    second = await provider.generate(ProviderRequest(prompt="hello DevMind"))

    assert first == second
    assert first.provider == "mock"
    assert "hello DevMind" in first.text
