"""Package for reading data from Pylontech (high voltage) BMS accessed via console."""
from __future__ import annotations

import asyncio
import logging

from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class Sensor:
    """Definition of inverter sensor and its attributes"""

    name: str
    unit: str
    value: Any

    def __str__(self):
        return f"{self.name}: {self.value} {self.unit}"


class Text(Sensor):
    """Sensor representing text value"""

    def __init__(self, name: str) -> None:
        super().__init__(name, " ", None)

    def set(self, source: str) -> Integer:
        self.value = source
        return self


class Integer(Sensor):
    """Sensor representing integer value"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "", None)

    def set(self, source: str) -> Integer:
        self.value = int(source)
        return self


class Percent(Sensor):
    """Sensor representing percent value"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "%", None)

    def set(self, source: str) -> Percent:
        self.value = int(source.replace("%", ""))
        return self


class Current(Sensor):
    """Sensor representing current [A]"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "A", None)

    def set(self, source: str, divider: int = 1000) -> Current:
        try:
            self.value = int(source) / divider
        except ValueError:
            self.value = int(source.replace("mA", "")) / divider
        return self


class Voltage(Sensor):
    """Sensor representing voltage [V]"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "V", None)

    def set(self, source: str, divider: int = 1000) -> Voltage:
        self.value = int(source) / divider
        return self


class ChargeAh(Sensor):
    """Sensor representing charge [Ah]"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "Ah", None)

    def set(self, source: str, divider: int = 1000) -> ChargeAh:
        self.value = int(source) / divider
        return self


class ChargeWh(Sensor):
    """Sensor representing charge [Wh]"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "Wh", None)

    def set(self, source: str, divider: int = 1) -> ChargeWh:
        self.value = int(source) / divider
        return self


class Temp(Sensor):
    """Sensor representing temperature [C]"""

    def __init__(self, name: str) -> None:
        super().__init__(name, "C", None)

    def set(self, source: str) -> Temp:
        self.value = int(source) / 1000
        return self


class Command(object):
    """Superclass for console commands."""


class UnitCommand(Command):
    """Pylontech BMS console command 'unit'."""

    def __init__(self, lines: tuple[str]) -> None:
        self.values = []
        for line in lines[2:]:
            self.values.append(UnitValues(line))

    def __str__(self) -> str:
        result = ""
        for val in self.values:
            result += str(val)
            result += "\n"
        return result


class UnitValues:
    """Class representing parameters of a unit (battery module)."""

    def __init__(self, line: str) -> None:
        chunks = line.split()
        self.index = Integer("Index").set(chunks[0])
        self.volt = Voltage("Voltage").set(chunks[1])
        self.curr = Current("Current").set(chunks[2])
        self.temp = Temp("Temperature").set(chunks[3])
        self.cell_temp_low = Temp("Lowest cell temperature").set(chunks[4])
        self.cell_temp_high = Temp("Highest cell temperature").set(chunks[5])
        self.cell_volt_low = Voltage("Lowest cell voltage").set(chunks[6])
        self.cell_bolt_high = Voltage("Highest cell voltage").set(chunks[7])
        self.base_state = Text("Basic state").set(chunks[8])
        self.volt_state = Text("Voltage state").set(chunks[9])
        self.temp_state = Text("Temperature state").set(chunks[10])
        self.charge_ah_perc = Percent("Charge Ah %").set(chunks[11])
        self.charge_ah = ChargeAh("Charge Ah").set(chunks[12])
        self.charge_wh_perc = Percent("Charge Wh %").set(chunks[14])
        self.charge_wh_wh = ChargeWh("Charge Wh").set(chunks[15])
        # self.Time

    def __str__(self):
        result = ""
        for each in vars(self).values():
            result += str(each)
            result += "\n"
        return result


class PwrCommand(Command):
    """Pylontech BMS console command 'pwr'."""

    def __init__(self, lines: tuple[str]) -> None:
        self.avg_temp = Temp("Average temperature").set(lines[0].split()[2])
        self.dc_voltage = Voltage("DC Voltage").set(lines[1].split()[3])
        self.bat_voltage = Voltage("Bat Voltage").set(lines[2].split()[3])
        chunks = lines[4].split()
        self.volt = Voltage("Voltage").set(chunks[0])
        self.curr = Current("Current").set(chunks[1])
        self.temp = Temp("Temperature").set(chunks[2])
        self.cell_temp_low = Temp("Lowest cell temperature").set(chunks[3])
        self.cell_temp_high = Temp("Highest cell temperature").set(chunks[4])
        self.cell_volt_low = Voltage("Lowest cell voltage").set(chunks[5])
        self.cell_bolt_high = Voltage("Highest cell voltage").set(chunks[6])
        self.unit_temp_low = Temp("Lowest unit temperature").set(chunks[7])
        self.unit_temp_high = Temp("Highest unit temperature").set(chunks[8])
        self.unit_volt_low = Voltage("Lowest unit voltage").set(chunks[9])
        self.unit_volt_high = Voltage("Highest unit voltage").set(chunks[10])
        self.base_state = Text("Basic state").set(chunks[11])
        self.volt_state = Text("Voltage state").set(chunks[12])
        self.curr_state = Text("Current state").set(chunks[13])
        self.temp_state = Text("Temperature state").set(chunks[14])
        self.charge_ah_perc = Percent("Charge Ah %").set(chunks[15])
        self.charge_ah = ChargeAh("Charge Ah").set(chunks[16])
        self.charge_wh_perc = Percent("Charge Wh %").set(chunks[18])
        self.charge_wh_wh = ChargeWh("Charge Wh").set(chunks[19])
        # time
        self.cell_volt_state = Text("Cell voltage state").set(chunks[23])
        self.cell_temp_state = Text("Cell temperature state").set(chunks[24])
        self.unit_volt_state = Text("Unit voltage state").set(chunks[25])
        self.unit_temp_state = Text("Unit tempeature state").set(chunks[26])
        self.error_code = Text("Error code").set(chunks[27])

    def __str__(self):
        result = ""
        for each in vars(self).values():
            result += str(each)
            result += "\n"
        return result


class BatCommand(Command):
    """Pylontech BMS console command 'bat'."""

    def __init__(self, lines: tuple[str]) -> None:
        self.avg_temp = Temp("Average Temperature").set(lines[1].split()[1])
        self.charge_curr = Current("Charge Current").set(lines[2].split()[2])
        self.discharge_curr = Current("Discharge Current").set(lines[3].split()[2])
        self.b_state = Text("Bat State").set(lines[4].split()[1])
        self.bal_volt = Voltage("Bat Voltage").set(lines[5].split()[1], 10)
        self.values = []
        for line in lines[7:]:
            self.values.append(BatValues(line))

    def __str__(self) -> str:
        result = ""
        for val in vars(self).values():
            result += str(val)
            result += "\n"
        return result


class BatValues:
    """Class representing paramters of a battery cell."""

    def __init__(self, line) -> None:
        chunks = line.split()
        self.bat = chunks[0]
        self.volt = int(chunks[1]) / 1000
        self.curr = int(chunks[2]) / 1000
        self.tempr = int(chunks[3]) / 1000
        self.v_state = chunks[4]
        self.t_state = chunks[5]
        self.charge_ah_perc = chunks[6]
        self.charge_ah = chunks[7]
        self.charge_wh_perc = chunks[8]
        self.charge_wh = chunks[9]
        self.bal = chunks[10]
        # self.Time

    def __str__(self):
        return f"""Bat: {self.bat}
Volt: {self.volt} V
Curr: {self.curr} A
Tempr: {self.tempr} C
v_state: {self.v_state}
t_state: {self.t_state}
coulomb_AH: {self.charge_ah_perc} ({self.charge_ah} mAH)
coulomb_WH: {self.charge_wh_perc} ({self.charge_wh} WH)
bal: {self.bal}"""


class InfoCommand(Command):
    """Pylontech BMS console command 'info'."""

    def __init__(self, lines: tuple[str]) -> None:
        self.device_address = Integer("Device address").set(lines[0].split()[3])
        self.manufacturer = Text("Manufacturer").set(lines[1].split()[2])
        self.device_name = Text("Device name").set(lines[2].split()[3])
        self.board_version = Text("Board version").set(lines[3].split()[3])
        self.main_sw_version = Text("Main Soft version").set(lines[4].split()[4])
        self.sw_version = Text("Soft version").set(lines[5].split()[3])
        self.boot_version = Text("Boot version").set(lines[6].split()[3])
        self.comm_version = Text("Comm version").set(lines[7].split()[3])
        self.release_date = Text("Release Date").set(lines[8].split()[3])
        self.pcba_barcode = Text("PCBA Barcode").set(lines[10].split()[3])
        self.module_barcode = Text("Module Barcode").set(lines[11].split()[3])
        self.pwr_supply_barcode = Text("PowerSupply Barcode").set(lines[12].split()[3])
        self.device_test_time = Text("Device Test Time").set(lines[13].split()[4])
        self.specification = Text("Specification").set(lines[14].split()[2])
        self.cell_number = Integer("Cell Number").set(lines[15].split()[3])
        self.max_discharge_current = Current("Max Discharge Curr").set(
            lines[16].split()[4]
        )
        self.max_charge_current = Current("Max Charge Curr").set(lines[17].split()[4])
        self.shut_circuit = Text("Shut Circuit").set(lines[18].split()[3])
        self.relay_feedback = Text("Relay Feedback").set(lines[19].split()[3])

        bmus = lines[20:]
        self.bmu_modules = []
        self.bmu_pcbas = []

        for line in bmus:
            if line.startswith("Module"):
                self.bmu_modules.insert(0, line.split()[2])
            if line.startswith("PCBA"):
                self.bmu_pcbas.insert(0, line.split()[2])

    def __str__(self) -> str:
        result = ""
        for val in vars(self).values():
            result += str(val)
            result += "\n"
        return result


class PylontechConsole(object):
    """Pylontech BMS console connection class"""

    _END_PROMPTS = ("Command completed successfully", "$$")

    def __init__(self, host: str, port: int) -> None:
        self.host: str = host
        self.port: int = port
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None

    async def _exec_cmd(self, cmd: str) -> tuple[str]:
        """Send the command to BMS and parse the response."""
        self.writer.write((cmd + "\r").encode("ascii"))
        await self.writer.drain()
        lines = []
        linebytes = bytearray()
        while linebytes != b"pylon>":
            # Read it by smaller chunks since on linux
            # large reads somehow weirdly do not work
            data = await self.reader.read(120)
            for i in data:
                # there seem to be mix of LF and CR+LF line endings
                if i != 13 and i != 10:
                    linebytes.append(i)
                else:
                    if len(linebytes) > 0:
                        line = linebytes.decode("ascii")
                        if not line in self._END_PROMPTS:
                            lines.append(line)
                        linebytes = bytearray()
        if lines.pop(0) != cmd:
            raise ValueError()
        if lines.pop(0) != "@":
            raise ValueError()
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Response lines:")
            for each in lines:
                _LOGGER.debug(each)
        return lines

    async def connect(self) -> None:
        """Connect to BMS console."""
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port)

    async def disconnect(self) -> None:
        """Diconnect from BMS console."""
        if self.reader is not None:
            self.writer.close()
            await self.writer.wait_closed()
            self.writer = None

    async def bat(self) -> BatCommand:
        """Invoke the 'bat' console command."""
        return BatCommand(await self._exec_cmd("bat"))

    async def info(self) -> InfoCommand:
        """Invoke the 'info' console command."""
        return InfoCommand(await self._exec_cmd("info"))

    async def pwr(self) -> PwrCommand:
        """Invoke the 'pwr' console command."""
        return PwrCommand(await self._exec_cmd("pwr"))

    async def unit(self) -> UnitCommand:
        """Invoke the 'unit' console command."""
        return UnitCommand(await self._exec_cmd("unit"))
