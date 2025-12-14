from server.games.monopoly import MonopolyGame
from server.models.room import Room, RoomPlayer


def test_monopoly_disconnect_forfeits_and_advances_turn():
    room = Room(room_id="r1", name="Monopoly", game_type="monopoly", max_players=2, min_players=2, host_id="u1")
    room.add_player(RoomPlayer(user_id="u1", nickname="U1", avatar="👤", is_host=True, is_ready=True))
    room.add_player(RoomPlayer(user_id="u2", nickname="U2", avatar="👤", is_host=False, is_ready=True))

    game = MonopolyGame(room)
    game.init_game()

    # 模拟 u1 已购买地块 1
    game.tiles[1]["owner"] = "u1"
    game.players["u1"]["properties"] = [1]

    msg = game.handle_disconnect("u1")

    assert game.players["u1"]["bankrupt"] is True
    assert game.players["u1"]["money"] == 0
    assert game.tiles[1]["owner"] is None
    assert game.current_player == "u2"

    assert msg["type"] == "game_action"
    assert msg["action"] == "player_disconnected"
    assert msg["user_id"] == "u1"
