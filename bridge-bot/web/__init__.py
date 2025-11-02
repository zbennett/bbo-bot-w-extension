"""
Web Dashboard Module
Provides a real-time web interface for bridge bot visualization
"""

from .dashboard import (
    app,
    socketio,
    start_server,
    update_new_deal,
    update_card_played,
    update_bid,
    update_contract,
    update_recommendation,
    update_dd_analysis,
    update_active_player
)

__all__ = [
    'app',
    'socketio',
    'start_server',
    'update_new_deal',
    'update_card_played',
    'update_bid',
    'update_contract',
    'update_recommendation',
    'update_dd_analysis',
    'update_active_player'
]
