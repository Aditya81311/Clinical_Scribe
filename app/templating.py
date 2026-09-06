from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates")


def timeago(dt):
    from datetime import datetime
    if dt is None:
        return ""
    delta = datetime.utcnow() - dt
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    minutes = int(seconds // 60)
    if minutes < 60:
        return f"{minutes}m ago"
    hours = int(minutes // 60)
    if hours < 24:
        return f"{hours}h ago"
    days = int(hours // 24)
    if days < 30:
        return f"{days}d ago"
    return dt.strftime("%d %b %Y")


templates.env.filters["timeago"] = timeago
