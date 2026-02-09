# pylint: disable=line-too-long
from config_loader import GuildConfig, GuildConfigLoader


def test_get_functions():
    """
    Test the get functions of the GuildConfig class.
    """

    gc = GuildConfig.load(1296495299870720033)

    cr_channel = gc.get_creator_by_channel_id(1363465167152615445)

    cr_category = gc.get_creator_by_category_id(1363464962592342217)

    assert cr_channel.general.name == cr_category.general.name, "Get functions are not working as expected"


def test_loading_all_guilds():
    """
    Test the loading of all guilds.
    """

    gcl = GuildConfigLoader()
    assert len(gcl.guilds) > 0, "No guilds loaded"
    assert isinstance(
        gcl.guilds[0], GuildConfig), "First guild is not a GuildConfig object"

    first_guild = gcl.guilds[0]
    print(first_guild)


if __name__ == '__main__':
    test_get_functions()
    test_loading_all_guilds()
    print("All tests passed.")
