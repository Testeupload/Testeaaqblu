import asyncio
from bleak import BleakScanner

async def run_scan():
    print("Procurando dispositivos Bluetooth...")
    devices = await BleakScanner.discover()
    for d in devices:
        print(f"Dispositivo encontrado: {d.name} ({d.address})")

async def main():
    await run_scan()

if __name__ == "__main__":
    asyncio.run(main())


