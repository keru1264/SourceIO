from pprint import pprint

from SourceIO.library.utils import TinyPath
from SourceIO.library.utils.kv_parser import ValveKeyValueParser
from SourceIO.library.utils.s1_keyvalues import KVParser


def test_kv1_duplicated_keys():
    data = """FileSystem
{
	SearchPaths
	{
		Game_LowViolence	csgo_lv // Perfect World content override

		Game	csgo
		Game	csgo_imported
		Game	csgo_core
		Game	core

		Mod		csgo
		Mod		csgo_imported
		Mod		csgo_core

		AddonRoot			csgo_addons
		OfficialAddonRoot	csgo_community_addons

		LayeredGameRoot		"../game_otherplatforms/etc" [$MOBILE || $ETC_TEXTURES] //Some platforms do not support DXT compression. ETC is a well-supported alternative.
		LayeredGameRoot		"../game_otherplatforms/low_bitrate" [$MOBILE]
	}

	"UserSettingsPathID"	"USRLOCAL"
	"UserSettingsFileEx"	"cs2_"
}"""

    parser = ValveKeyValueParser(None, (data, ""))
    parser.parse()
    root = parser.tree
    search_paths = root["FileSystem"]["SearchPaths"]
    game = search_paths["Game"]
    games = search_paths.get_multiple("game")
    all_paths = search_paths.items()
    print(root["FileSystem"]["SearchPaths"])
    print(game)
    print(games)
    print(list(all_paths))