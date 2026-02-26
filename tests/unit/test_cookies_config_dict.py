import pytest

from browser_launcher.cookies import CookieConfig


@pytest.mark.unit
def test_cookieconfig_dict_structure():
    config: dict[str, dict] = {}
    cc = CookieConfig(config)
    user, env, domain = "default", "prod", "artists_apple_com"
    # Update/add two cookies
    cc.update_cookie_cache(user, env, domain, "myacinfo", "VAL1")
    cc.update_cookie_cache(user, env, domain, "dqsid", "VAL2")
    # Check config structure - now at users.{user}.{env}.cookies.{name}
    cookies = config["users"][user][env]["cookies"]
    assert isinstance(cookies, dict)
    assert set(cookies.keys()) == {"myacinfo", "dqsid"}
    # Check values and domain field
    assert cookies["myacinfo"]["value"] == "VAL1"
    assert cookies["myacinfo"]["domain"] == domain
    assert cookies["dqsid"]["value"] == "VAL2"
    assert cookies["dqsid"]["domain"] == domain
    # Save and reload
    cc.save_cookie_cache(user, env, domain, cc.load_cookie_cache(user, env, domain))
    cookies2 = config["users"][user][env]["cookies"]
    assert len(cookies2) == 2
    # Prune (should keep both as valid)
    cc.prune_expired_cookies(user, env, domain)
    assert set(config["users"][user][env]["cookies"].keys()) == {"myacinfo", "dqsid"}
    # Clear
    cc.clear_cookie_cache(user, env, domain)
    assert (
        len(
            [
                c
                for c in config["users"][user][env]["cookies"].values()
                if c.get("domain") == domain
            ]
        )
        == 0
    )
