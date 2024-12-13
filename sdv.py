import xml.etree.ElementTree as ET
def analyze_xml(xml_content):
    try:
        root = ET.fromstring(xml_content)
        player_name_element = root.find("player/name")
        player_name = player_name_element.text if player_name_element is not None else "Unknown Player"

        game_version_element = root.find(".//gameVersion")
        game_version = game_version_element.text if game_version_element is not None else "Unknown Game Version"
        parsed_data = {
            "player_name": player_name,
            "game_version": game_version,
        }
        return parsed_data
    except ET.ParseError as e:
        return {"error": str(e)}