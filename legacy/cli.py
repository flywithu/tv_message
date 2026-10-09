"""Command-line interface for Samsung TV control."""

import asyncio
import json
import logging
import sys
from typing import Any

import click

from .samsung_tv import SamsungTV
from .messages import PresetMessages, MessageTemplate

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger(__name__)


def format_output(data: Any, json_output: bool = False) -> str:
    """Format output for display."""
    if json_output:
        if isinstance(data, dict):
            return json.dumps(data, indent=2)
        return json.dumps({"result": data})
    return str(data)


@click.group()
@click.option(
    "--host",
    default="192.168.10.38",
    help="Samsung TV IP address",
)
@click.option(
    "--port",
    default=8002,
    type=int,
    help="Samsung TV port",
)
@click.option(
    "--json",
    "json_output",
    is_flag=True,
    help="Output as JSON",
)
@click.pass_context
def cli(ctx: click.Context, host: str, port: int, json_output: bool) -> None:
    """Samsung TV CLI - Control your TV from the command line."""
    ctx.ensure_object(dict)
    ctx.obj["host"] = host
    ctx.obj["port"] = port
    ctx.obj["json_output"] = json_output


@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Get TV status."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_status():
        power = await tv.get_power_state()
        result = {"power": power}
        
        if power == "on":
            volume = await tv.get_volume()
            muted = await tv.get_mute()
            app = await tv.get_current_app()
            device_info = await tv.get_device_info()
            
            result["volume"] = volume
            result["muted"] = muted
            result["current_app"] = app
            if device_info:
                result["device_info"] = device_info
        
        return result
    
    try:
        result = asyncio.run(get_status())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def on(ctx: click.Context) -> None:
    """Turn on TV."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def turn_on():
        result = await tv.turn_on()
        return {"success": result}
    
    try:
        result = asyncio.run(turn_on())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def off(ctx: click.Context) -> None:
    """Turn off TV."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def turn_off():
        result = await tv.turn_off()
        return {"success": result}
    
    try:
        result = asyncio.run(turn_off())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("volume", type=int)
@click.pass_context
def volume(ctx: click.Context, volume: int) -> None:
    """Set volume (0-100)."""
    if not 0 <= volume <= 100:
        click.echo("Volume must be between 0 and 100", err=True)
        sys.exit(1)
    
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_vol():
        result = await tv.set_volume(volume)
        return {"success": result, "volume": volume}
    
    try:
        result = asyncio.run(set_vol())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("state", type=click.Choice(["on", "off"], case_sensitive=False))
@click.pass_context
def mute(ctx: click.Context, state: str) -> None:
    """Mute or unmute."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    mute_value = state.lower() == "on"
    
    async def set_mute():
        result = await tv.set_mute(mute_value)
        return {"success": result, "muted": mute_value}
    
    try:
        result = asyncio.run(set_mute())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("key")
@click.pass_context
def key(ctx: click.Context, key: str) -> None:
    """Send remote control key.
    
    Common keys: KEY_POWER, KEY_HOME, KEY_MENU, KEY_BACK, 
                 KEY_UP, KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_ENTER,
                 KEY_PLAY, KEY_PAUSE, KEY_NEXT, KEY_PREV
    """
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def send_key():
        result = await tv.send_key(key)
        return {"success": result, "key": key}
    
    try:
        result = asyncio.run(send_key())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def app(ctx: click.Context) -> None:
    """Get current app."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_app():
        result = await tv.get_current_app()
        return {"current_app": result}
    
    try:
        result = asyncio.run(get_app())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("app_name")
@click.pass_context
def launch(ctx: click.Context, app_name: str) -> None:
    """Launch an app."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def launch_app():
        result = await tv.launch_app(app_name)
        return {"success": result, "app": app_name}
    
    try:
        result = asyncio.run(launch_app())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("message")
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def message(ctx: click.Context, message: str, duration: int) -> None:
    """Display message on TV screen."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def show_msg():
        result = await tv.show_message(message, duration)
        return {"success": result, "message": message, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("channel", type=int)
@click.pass_context
def channel(ctx: click.Context, channel: int) -> None:
    """Change TV channel (0-999)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_ch():
        result = await tv.set_channel(channel)
        return {"success": result, "channel": channel}
    
    try:
        result = asyncio.run(set_ch())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("source", type=click.Choice(["HDMI1", "HDMI2", "HDMI3", "HDMI4", "TV"]))
@click.pass_context
def source(ctx: click.Context, source: str) -> None:
    """Set input source (HDMI1/2/3/4 or TV)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_src():
        result = await tv.set_input_source(source)
        return {"success": result, "source": source}
    
    try:
        result = asyncio.run(set_src())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def get_source(ctx: click.Context) -> None:
    """Get current input source."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_src():
        result = await tv.get_input_source()
        return {"source": result}
    
    try:
        result = asyncio.run(get_src())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("brightness", type=int)
@click.pass_context
def brightness(ctx: click.Context, brightness: int) -> None:
    """Set brightness (0-100)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_bright():
        result = await tv.set_brightness(brightness)
        return {"success": result, "brightness": brightness}
    
    try:
        result = asyncio.run(set_bright())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def get_brightness(ctx: click.Context) -> None:
    """Get current brightness."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_bright():
        result = await tv.get_brightness()
        return {"brightness": result}
    
    try:
        result = asyncio.run(get_bright())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("contrast", type=int)
@click.pass_context
def contrast(ctx: click.Context, contrast: int) -> None:
    """Set contrast (0-100)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_contr():
        result = await tv.set_contrast(contrast)
        return {"success": result, "contrast": contrast}
    
    try:
        result = asyncio.run(set_contr())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("color", type=int)
@click.pass_context
def color(ctx: click.Context, color: int) -> None:
    """Set color saturation (0-100)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_color_sat():
        result = await tv.set_color(color)
        return {"success": result, "color": color}
    
    try:
        result = asyncio.run(set_color_sat())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.argument("minutes", type=int)
@click.pass_context
def sleep_timer(ctx: click.Context, minutes: int) -> None:
    """Set sleep timer (1-180 minutes)."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_timer():
        result = await tv.set_sleep_timer(minutes)
        return {"success": result, "minutes": minutes}
    
    try:
        result = asyncio.run(set_timer())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def apps(ctx: click.Context) -> None:
    """Get list of installed apps."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_apps():
        result = await tv.get_supported_apps()
        return {"apps": result}
    
    try:
        result = asyncio.run(get_apps())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def channels(ctx: click.Context) -> None:
    """Get list of channels."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_channels():
        result = await tv.get_supported_channels()
        return {"channels": result}
    
    try:
        result = asyncio.run(get_channels())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def settings(ctx: click.Context) -> None:
    """Get TV settings."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def get_settings():
        result = await tv.get_tv_settings()
        return {"settings": result}
    
    try:
        result = asyncio.run(get_settings())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--enabled",
    is_flag=True,
    help="Enable HDR (default is disable)",
)
@click.pass_context
def hdr(ctx: click.Context, enabled: bool) -> None:
    """Enable/disable HDR."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    
    async def set_hdr():
        result = await tv.set_hdr(enabled)
        return {"success": result, "hdr_enabled": enabled}
    
    try:
        result = asyncio.run(set_hdr())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def reboot(ctx: click.Context) -> None:
    """Reboot TV."""
    if click.confirm("Are you sure you want to reboot the TV?"):
        tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
        
        async def tv_reboot():
            result = await tv.reboot()
            return {"success": result}
        
        try:
            result = asyncio.run(tv_reboot())
            click.echo(format_output(result, ctx.obj["json_output"]))
        except Exception as err:
            click.echo(f"Error: {err}", err=True)
            sys.exit(1)
    else:
        click.echo("Reboot cancelled")


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_sleep(ctx: click.Context, duration: int) -> None:
    """Show sleep time message: '지금은 취침시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.sleep_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_rest(ctx: click.Context, duration: int) -> None:
    """Show rest time message: '지금은 휴식시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.rest_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_study(ctx: click.Context, duration: int) -> None:
    """Show study time message: '공부 시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.study_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_break(ctx: click.Context, duration: int) -> None:
    """Show break time message: '휴식 시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.break_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_meal(ctx: click.Context, duration: int) -> None:
    """Show meal time message: '식사 시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.meal_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_exercise(ctx: click.Context, duration: int) -> None:
    """Show exercise time message: '운동 시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.exercise_time()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--duration",
    default=5,
    type=int,
    help="Display duration in seconds (1-10)",
)
@click.pass_context
def msg_wake(ctx: click.Context, duration: int) -> None:
    """Show wake up message: '일어날 시간입니다'."""
    tv = SamsungTV(ctx.obj["host"], ctx.obj["port"])
    msg = PresetMessages.wake_up()
    
    async def show_msg():
        result = await tv.show_message(msg, duration)
        return {"success": result, "message": msg, "duration": duration}
    
    try:
        result = asyncio.run(show_msg())
        click.echo(format_output(result, ctx.obj["json_output"]))
    except Exception as err:
        click.echo(f"Error: {err}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context
def presets(ctx: click.Context) -> None:
    """List all preset messages."""
    presets = PresetMessages.get_all_presets()
    click.echo(format_output(presets, ctx.obj["json_output"]))


if __name__ == "__main__":
    cli(obj={})
