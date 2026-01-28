async def execute(context):
    config = context.get("config", {})
    return {
        "memory": {
            "type": "buffer_window",
            "window_size": config.get("window_size", 5)
        }
    }
