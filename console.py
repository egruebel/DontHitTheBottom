from console_controller import RoundRobinConsole

def init():
    global dhtb_console
    dhtb_console = RoundRobinConsole()
    dhtb_console.start_console()

