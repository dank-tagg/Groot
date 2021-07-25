
from discord.ext import ipc
from quart import (Quart, Response, abort, redirect, render_template, request,
                   url_for)
from quart_auth import AuthManager, AuthUser, Unauthorized
from quart_auth import login_required as auth_required
from quart_auth import login_user, logout_user
from quart_discord import DiscordOAuth2Session
from werkzeug.exceptions import HTTPException
from os import environ
from dotenv import load_dotenv

load_dotenv()

app = Quart(__name__)
ipc_client = ipc.Client(secret_key="GrootBotAdmin")
app.config["SECRET_KEY"] = "Groot"
app.config["DISCORD_CLIENT_ID"] = 812395879146717214
app.config["DISCORD_CLIENT_SECRET"] = "83JNyFPtPQBZj6qz95c3uHPTHjc7aQhd"
app.config["DISCORD_REDIRECT_URI"] = "http://www.grootdiscordbot.xyz/api/callback"


discord = DiscordOAuth2Session(app)


# Auth
AuthManager(app)

# Routes


@app.route("/")
async def home():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("index.html", user=user)

@app.route("/about")
async def about():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("about.html", user=user)
    
@app.route("/support")
async def support():
    user = None
    if await discord.authorized:
        user = await discord.fetch_user()
    return await render_template("support.html", user=user)

@app.route("/stats")
async def stats():
    stats = await ipc_client.request("get_stats")
    return await render_template(
        "stats.html", 
        users=f"{stats['users']:,}", 
        guilds=f"{stats['guilds']:,}", 
        commands=f"{stats['commands']:,}",
        uptime=f"{stats['uptime']}"
    )

# Shortcuts
@app.route("/invite")
async def invite():
    return redirect("https://discord.com/oauth2/authorize?client_id=812395879146717214&scope=bot")

@app.route("/vote")
async def vote():
    return redirect("https://top.gg/bot/812395879146717214/vote")

@app.route("/server")
async def server():
    return redirect("https://discord.gg/nUUJPgemFE")

@app.route("/source")
async def source():
    return redirect("https://github.com/dank-tagg/Groot")

# API (discord etc)


@app.route("/api/login")
async def login():
    return await discord.create_session(scopes=["identify", "guilds"])

@app.route("/api/logout")
async def logout():
    discord.revoke()
    logout_user()
    return redirect(url_for("home"))

@app.route("/api/callback")
async def callback():
    try:
        await discord.callback()
    except Exception:
        return redirect(url_for("login"))
    user = await discord.fetch_user()
    login_user(AuthUser(user.id))
    return await render_template("index.html", user=user)

@app.route("/api/webhook/<source>", methods=["POST"])
async def webhook(source):
    data = await request.get_json(force=True)

    if request.headers["Authorization"] != environ.get("AUTH"):
        abort(403)

    data["source"] = source

    if source == "dbl":
        data["user"] = data["id"]

    res = await ipc_client.request("on_vote", vote_data=data)
    return Response(status=200)


@app.errorhandler(Exception)
async def handle_exception(error):
    name = "Internal Server Error"
    description = "Woops, something went wrong on our side. Sorry for the inconvenience!"

    if isinstance(error, HTTPException):
        name = error.name
        description = error.description

    return await render_template("error.html", error_name=name, error_msg=description)


if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", debug=True)
    except OSError:
        print("Port is already in use.")
