"""
游戏会话管理：将服务器消息桥接到 GamePlugin，并把插件输入发送回服务器。

目标：
- MainWindow 只负责 UI 与消息分发
- GameSession 负责插件生命周期与网络映射
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from client.net import AuthManager, WebSocketManager
from client.plugins import GAME_PLUGINS
from client.plugins.base import EventType, GameContext, GamePlugin, NetworkEvent, PlayerInfo, RoomState


@dataclass
class RoomSnapshot:
    room_id: str
    room: Dict[str, Any]
    players: list[Dict[str, Any]]


class GameSession:
    """单房间游戏会话（MVP：每次只玩一个房间/游戏）"""

    def __init__(self, auth: AuthManager, ws: WebSocketManager, assets_dir: Path, cache_dir: Path):
        self._auth = auth
        self._ws = ws
        self._assets_dir = assets_dir
        self._cache_dir = cache_dir

        self.room: Optional[RoomSnapshot] = None
        self.game_type: Optional[str] = None
        self.plugin: Optional[GamePlugin] = None

    def set_room_snapshot(self, room_id: str, room: Dict[str, Any], players: list[Dict[str, Any]]):
        self.room = RoomSnapshot(room_id=str(room_id), room=room or {}, players=players or [])

    def _build_room_state(self) -> RoomState:
        if not self.room:
            raise RuntimeError("room snapshot missing")

        current_players = [
            PlayerInfo(
                user_id=str(p.get("user_id", "")),
                nickname=str(p.get("nickname", "")),
                avatar_url=str(p.get("avatar", "")),
                team_id=p.get("team"),
                is_ready=bool(p.get("is_ready", False)),
                is_host=bool(p.get("is_host", False)),
            )
            for p in (self.room.players or [])
        ]

        game_type = str((self.room.room or {}).get("game_type") or "")
        max_players = int((self.room.room or {}).get("max_players") or max(len(current_players), 2))

        return RoomState(
            room_id=self.room.room_id,
            game_type=game_type,
            max_players=max_players,
            current_players=current_players,
        )

    def _build_context(self) -> GameContext:
        user_id = ""
        nickname = ""
        if self._auth.session:
            user_id = self._auth.session.user_id
            nickname = self._auth.session.nickname or self._auth.session.username

        local_user = PlayerInfo(user_id=user_id, nickname=nickname or user_id or "Player")

        def send_network(event: NetworkEvent) -> None:
            if event.type != EventType.INPUT:
                return

            raw = dict(event.payload or {})
            action = raw.get("action") or raw.get("type") or ""
            data = dict(raw)
            data.pop("action", None)
            data.pop("type", None)

            if not action:
                return

            self._ws.send("game_action", {"action": action, "data": data}, requires_ack=False)

        return GameContext(
            assets_path=str(self._assets_dir),
            cache_path=str(self._cache_dir),
            local_user=local_user,
            send_network=send_network,
        )

    def start(self, game_type: str, init_payload: Dict[str, Any]) -> GamePlugin:
        """收到 game_start 后启动插件，并用 init_payload 进行一次初始化同步。"""
        if not self.room:
            raise RuntimeError("room snapshot missing")

        self.game_type = game_type

        plugin_cls = GAME_PLUGINS.get(game_type)
        if not plugin_cls:
            raise ValueError(f"unknown game_type: {game_type}")

        plugin = plugin_cls()
        context = self._build_context()
        room_state = self._build_room_state()

        plugin.load(context)
        plugin.join_room(room_state)
        plugin.start_game()

        # 通用：将 game_start 作为 STATE 注入（便于回合制游戏初始化 UI）
        try:
            plugin.on_network(
                NetworkEvent(type=EventType.STATE, payload={"action": "game_start", **(init_payload or {})})
            )
        except Exception:
            pass

        # 初始状态注入（不同游戏字段不同，尽量做兼容）
        if game_type == "shooter2d":
            plugin.on_network(
                NetworkEvent(
                    type=EventType.SYNC,
                    payload={
                        "players": init_payload.get("players", []),
                        "bullets": init_payload.get("bullets", []),
                    },
                    frame_id=int(init_payload.get("frame_id") or 0),
                )
            )

        self.plugin = plugin
        return plugin

    def stop(self):
        if self.plugin:
            try:
                self.plugin.dispose()
            except Exception:
                pass
        self.plugin = None
        self.game_type = None

    def handle_game_action(self, payload: Dict[str, Any]):
        if not self.plugin:
            return
        action = payload.get("action")
        if not action:
            return
        # gomoku 插件使用 payload['action'] 分支
        self.plugin.on_network(NetworkEvent(type=EventType.STATE, payload={"action": action, **payload}))

    def handle_game_sync(self, payload: Dict[str, Any]):
        if not self.plugin:
            return
        state = payload.get("state") or {}
        frame_id = int(payload.get("frame_id") or 0)
        self.plugin.on_network(NetworkEvent(type=EventType.SYNC, payload=state, frame_id=frame_id))

    def handle_game_end(self, payload: Dict[str, Any]):
        if not self.plugin:
            return
        self.plugin.on_network(NetworkEvent(type=EventType.SYSTEM, payload={"action": "game_end", **payload}))

    def handle_game_private(self, payload: Dict[str, Any]):
        if not self.plugin:
            return
        self.plugin.on_network(NetworkEvent(type=EventType.SYSTEM, payload=payload or {}))

    def handle_game_action_response(self, payload: Dict[str, Any]):
        if not self.plugin:
            return
        if not payload.get("success"):
            return
        # 仅转发包含 action 的“私有结果”（例如 seer_result）
        action = payload.get("action")
        if not action:
            return
        self.plugin.on_network(NetworkEvent(type=EventType.SYSTEM, payload=payload or {}))
