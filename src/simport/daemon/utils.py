import asyncio
import socketio

def create_sync_emitter(sio: socketio.AsyncServer, sid: str, loop: asyncio.AbstractEventLoop, event_name: str):
    """
    Creates a synchronous function that can emit events safely 
    from a background thread to the asyncio event loop.
    """
    def emit(payload: dict):
        asyncio.run_coroutine_threadsafe(
            sio.emit(event_name, payload, to=sid),
            loop
        )
    return emit
