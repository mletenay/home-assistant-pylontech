"""Package for reading data from Pylontech (high voltage) BMS.

The 'info' BMS command returns list of BMU from top to bottom.
Topmost unit, first in chain, right after BMS iself is reported as BMU #0.
The last in chain is BBU #n-1

However the 'unit' and 'bat' BMS commands seem to report units/cells
in reversed order !
Unit with index 1 is the last one in chain - BMU #n-1
Cells with index 0-14 are from the last unit in chain.
"""

from __future__ import annotations

import asyncio
from asyncio import StreamReader, StreamWriter
from dataclasses import dataclass
import logging
from typing import Any

_LOGGER = logging.getLogger(__name__)


@dataclass
class Sensor:
    """Definition of inverter sensor and its attributes."""

    name: str
    unit: str
    value: Any

    def __str__(self):
        """Return string representation of sensor."""
        return f"{self.name}: {self.value} {self.unit}"

    def set(self, source: str) -> Sensor:
        """Decode and set value from source string."""
        return self

    def setValue(self, source: str) -> Sensor:
        """Decode and set value from source line.

        The input line is assumed to be of a "Label : value" form,
        so the value starts after first ":" character.
        """
        self.set(source[source.index(":") + 1 :])
        return self


class HasSensors:
    """Supeclass for BMS types with sensors attributres."""

    def get_sensors(self) -> dict[str, Sensor]:
        """Return sensor values provided by the command."""
        return {k: v for k, v in vars(self).items() if isinstance(v, Sensor)}


class Text(Sensor):
    """Sensor representing text value."""

    def __init__(self, name: str) -> None:
        """Initialize the text sensor."""
        super().__init__(name, " ", None)

    def set(self, source: str) -> Text:
        """Decode and set value from source string."""
        self.value = source
        return self

    def fetch(self, source: list[str], lookup: str | None = None) -> Text:
        """Decode (if present) and set value (after : separator) from list of string."""
        if (lookup if lookup else self.name) in source[0]:
            self.value = source[0].split(":")[1]
            source.pop(0)
        return self


class Boolean(Sensor):
    """Sensor representing Y/N value."""

    def __init__(self, name: str) -> None:
        """Initialize the text sensor."""
        super().__init__(name, "Y/N", None)

    def set(self, source: str) -> Text:
        """Decode and set value from source string."""
        self.value = source in {"Y", "y"}
        return self


class Integer(Sensor):
    """Sensor representing integer value."""

    def __init__(self, name: str) -> None:
        """Initialize the integer sensor."""
        super().__init__(name, "", None)

    def set(self, source: str) -> Integer:
        """Decode and set value from source string."""
        self.value = int(source)
        return self

    def fetch(self, source: list[str], lookup: str | None = None) -> Integer:
        """Decode (if present) and set value (after : separator) from list of string."""
        if (lookup if lookup else self.name) in source[0]:
            self.value = int(source[0].split(":")[1])
            source.pop(0)
        return self


class Percent(Sensor):
    """Sensor representing percent value."""

    def __init__(self, name: str) -> None:
        """Initialize the percent sensor."""
        super().__init__(name, "%", None)

    def set(self, source: str) -> Percent:
        """Decode and set value from source string."""
        self.value = int(source.replace("%", ""))
        return self


class Current(Sensor):
    """Sensor representing current [A]."""

    def __init__(self, name: str) -> None:
        """Initialize the current sensor."""
        super().__init__(name, "A", None)

    def set(self, source: str, divider: int = 1000) -> Current:
        """Decode and set value from source string."""
        try:
            self.value = int(source) / divider
        except ValueError:
            self.value = int(source.replace("mA", "")) / divider
        return self

    def fetch(self, source: list[str], lookup: str | None = None) -> Current:
        """Decode (if present) and set value (after : separator) from list of string."""
        if (lookup if lookup else self.name) in source[0]:
            self.value = int(source[0].split(":")[1].replace("mA", ""))
            source.pop(0)
        return self


class Voltage(Sensor):
    """Sensor representing voltage [V]."""

    def __init__(self, name: str) -> None:
        """Initialize the voltage sensor."""
        super().__init__(name, "V", None)

    def set(self, source: str, divider: int = 1000) -> Voltage:
        """Decode and set value from source string."""
        self.value = int(source) / divider
        return self

    def setValue(self, source: str, divider: int = 1000) -> Sensor:
        """Decode and set value from source line.

        The input line is assumed to be of a "Label : value" form,
        so the value starts after first ":" character.
        """
        self.set(source[source.index(":") + 1 :], divider)
        return self


class ChargeAh(Sensor):
    """Sensor representing charge [Ah]."""

    def __init__(self, name: str) -> None:
        """Initialize the charge sensor."""
        super().__init__(name, "Ah", None)

    def set(self, source: str, divider: int = 1000) -> ChargeAh:
        """Decode and set value from source string."""
        self.value = int(source) / divider
        return self


class ChargeWh(Sensor):
    """Sensor representing charge [Wh]."""

    def __init__(self, name: str) -> None:
        """Initialize the charge sensor."""
        super().__init__(name, "Wh", None)

    def set(self, source: str, divider: int = 1) -> ChargeWh:
        """Decode and set value from source string."""
        self.value = int(source) / divider
        return self


class Temp(Sensor):
    """Sensor representing temperature [C]."""

    def __init__(self, name: str) -> None:
        """Initialize the temp sensor."""
        super().__init__(name, "C", None)

    def set(self, source: str) -> Temp:
        """Decode and set value from source string."""
        self.value = int(source) / 1000
        return self


class UnitCommand:
    """Pylontech BMS console command 'unit'."""

    def __init__(self, lines: tuple[str]) -> None:
        """Initialize the unit command."""
        self.values: list[UnitValues] = []
        nr_of_units = len(lines) - 1
        for line in lines[2:]:
            # unit values are presented in reversed oder, from bottom to top
            self.values.insert(0, UnitValues(line, nr_of_units))

    def __str__(self) -> str:
        """Return string representation of unit command."""
        result = ""
        for val in self.values:
            result += str(val)
            result += "\n"
        return result


class UnitValues(HasSensors):
    """Class representing parameters of a unit (battery module)."""

    def __init__(self, line: str, nr_of_units: int) -> None:
        """Initialize the unit values object."""
        chunks = line.split()
        self.position = Integer("Position").set(chunks[0])
        self.position.value = nr_of_units - self.position.value
        self.volt = Voltage("Voltage").set(chunks[1])
        self.curr = Current("Current").set(chunks[2])
        self.temp = Temp("Temperature").set(chunks[3])
        self.cell_temp_low = Temp("Lowest cell temperature").set(chunks[4])
        self.cell_temp_high = Temp("Highest cell temperature").set(chunks[5])
        self.cell_volt_low = Voltage("Lowest cell voltage").set(chunks[6])
        self.cell_volt_high = Voltage("Highest cell voltage").set(chunks[7])
        self.base_state = Text("Basic state").set(chunks[8])
        self.volt_state = Text("Voltage state").set(chunks[9])
        self.temp_state = Text("Temperature state").set(chunks[10])
        self.charge_ah_perc = Percent("Charge Ah %").set(chunks[11])
        self.charge_ah = ChargeAh("Charge Ah").set(chunks[12])
        self.charge_wh_perc = Percent("Charge Wh %").set(chunks[14])
        self.charge_wh_wh = ChargeWh("Charge Wh").set(chunks[15])
        # self.Time

    def __str__(self):
        """Return string representation of unit values."""
        result = ""
        for each in vars(self).values():
            result += str(each)
            result += "\n"
        return result


class PwrCommand(HasSensors):
    """Pylontech BMS console command 'pwr'."""

    def __init__(self, lines: tuple[str]) -> None:
        """Initialize the pwr command."""
        self.avg_temp = Temp("Average temperature").setValue(lines[0])
        self.dc_voltage = Voltage("DC Voltage").setValue(lines[1])
        self.bat_voltage = Voltage("Bat Voltage").setValue(lines[2])
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
        """Return string representation of pwr command."""
        result = ""
        for each in vars(self).values():
            result += str(each)
            result += "\n"
        return result


class BatCommand(HasSensors):
    """Pylontech BMS console command 'bat'."""

    def __init__(self, lines: tuple[str]) -> None:
        """Initialize the bat sensor."""
        self.avg_temp = Temp("Average Temperature").setValue(lines[1])
        self.charge_curr = Current("Charge Current").setValue(lines[2])
        self.discharge_curr = Current("Discharge Current").setValue(lines[3])
        self.b_state = Text("Bat State").setValue(lines[4])
        self.bal_volt = Voltage("Bat Voltage").setValue(lines[5], 10)
        self.values: list[BatValues] = []
        cell = len(lines) - 8  # bat returs cells in reverse units order
        for line in lines[7:]:
            self.values.append(BatValues(line, int(cell / 15)))
            cell = cell - 1

    def __str__(self) -> str:
        """Return string representation of bat command."""
        result = ""
        for val in vars(self).values():
            if val is not None:
                result += str(val)
                result += "\n"
        return result


class BatValues(HasSensors):
    """Class representing paramters of a battery cell."""

    def __init__(self, line: str, unit: int) -> None:
        """Initialize the bat values object."""
        chunks = line.split()
        self.unit = unit
        self.volt = Voltage("Cell voltage").set(chunks[1])
        self.curr = Current("Cell current").set(chunks[2])
        self.tempr = Temp("Cell temperature").set(chunks[3])
        self.v_state = Text("Cell voltage state").set(chunks[4])
        self.t_state = Text("Cell temperature state").set(chunks[5])
        self.charge_ah_perc = Percent("Cell charge Ah %").set(chunks[6])
        self.charge_ah = ChargeAh("Cell charge Ah").set(chunks[7])
        self.charge_wh_perc = Percent("Cell charge Wh %").set(chunks[8])
        self.charge_wh = ChargeWh("Cell charge Wh").set(chunks[9], 1000)
        self.bal = Text("Cell balance").set(chunks[10])
        # self.Time

    def __str__(self):
        """Return string representation of unit values."""
        result = ""
        for each in vars(self).values():
            result += str(each)
            result += "\n"
        return result


class InfoCommand(HasSensors):
    """Pylontech BMS console command 'info'."""

    def __init__(self, lines: tuple[str]) -> None:
        """Initialize the info command."""
        source = list(lines)
        self.device_address = Integer("Device address").fetch(source)
        self.manufacturer = Text("Manufacturer").fetch(source)
        self.device_name = Text("Device name").fetch(source)
        self.board_version = Text("Board version").fetch(source)
        self.hard_version = Text("Hard version").fetch(source, "Hard  version")
        self.main_sw_version = Text("Main Soft version").fetch(source)
        self.sw_version = Text("Soft version").fetch(source, "Soft  version")
        self.boot_version = Text("Boot version").fetch(source, "Boot  version")
        self.comm_version = Text("Comm version").fetch(source)
        self.release_date = Text("Release Date").fetch(source)
        self.barcode = Text("Barcode").fetch(source)
        self.pcba_barcode = Text("PCBA Barcode").fetch(source)
        self.module_barcode = Text("Module Barcode").fetch(source)
        self.pwr_supply_barcode = Text("PowerSupply Barcode").fetch(source)
        self.device_test_time = Text("Device Test Time").fetch(source)
        self.specification = Text("Specification").fetch(source)
        self.cell_number = Integer("Cell Number").fetch(source)
        self.max_discharge_current = Current("Max Discharge Curr").fetch(
            source, "Max Dischg Curr"
        )
        self.max_charge_current = Current("Max Charge Curr").fetch(source)
        self.shut_circuit = Text("Shut Circuit").fetch(source)
        self.relay_feedback = Text("Relay Feedback").fetch(source)
        self.new_board = Text("New Board").fetch(source)

        self.bmu_modules: list[str] = []
        self.bmu_pcbas: list[str] = []

        for line in source:
            if line.startswith("Module"):
                self.bmu_modules.insert(0, line.split()[2])
            if line.startswith("PCBA"):
                self.bmu_pcbas.insert(0, line.split()[2])

    def __str__(self) -> str:
        """Return string representation of info command."""
        result = ""
        for val in vars(self).values():
            if val is not None:
                result += str(val)
                result += "\n"
        return result


class PylontechBMS:
    """Pylontech BMS connection class."""

    _END_PROMPTS = ("Command completed successfully", "$$")

    def __init__(self, host: str, port: int) -> None:
        """Initialize the BMS object."""
        self.host: str = host
        self.port: int = port
        self.reader: StreamReader | None = None
        self.writer: StreamWriter | None = None
        self.bmus: tuple[str] = ()

    async def _exec_cmd(self, cmd: str) -> tuple[str]:
        """Send the command to BMS and parse the response."""
        self.writer.write((cmd + "\r").encode("ascii"))
        await asyncio.wait_for(self.writer.drain(), 2)
        lines = []
        linebytes = bytearray()
        while linebytes != b"pylon>":
            # Read it by smaller chunks since on linux
            # large reads somehow weirdly do not work
            data = await asyncio.wait_for(self.reader.read(120), 2)
            for i in data:
                # there seem to be mix of LF and CR+LF line endings
                if i not in (13, 10):
                    linebytes.append(i)
                elif len(linebytes) > 0:
                    line = linebytes.decode("ascii")
                    if line not in self._END_PROMPTS:
                        lines.append(line)
                    linebytes = bytearray()
        if lines.pop(0) != cmd:
            raise ValueError("wrong value")
        if lines.pop(0) != "@":
            raise ValueError("wrong value")
        if _LOGGER.isEnabledFor(logging.DEBUG):
            _LOGGER.debug("Response lines:")
            for each in lines:
                _LOGGER.debug(each)
        return lines

    async def connect(self) -> None:
        """Connect to BMS console."""
        self.reader, self.writer = await asyncio.wait_for(
            asyncio.open_connection(self.host, self.port), 5
        )

    async def disconnect(self) -> None:
        """Diconnect from BMS console."""
        if self.writer is not None:
            self.writer.close()
            await self.writer.wait_closed()
            self.reader = None
            self.writer = None

    async def bat(self) -> BatCommand:
        """Invoke the 'bat' console command."""
        return BatCommand(await self._exec_cmd("bat"))

    async def info(self) -> InfoCommand:
        """Invoke the 'info' console command."""
        result = InfoCommand(await self._exec_cmd("info"))
        self.bmus = tuple(result.bmu_modules)
        return result

    async def pwr(self) -> PwrCommand:
        """Invoke the 'pwr' console command."""
        return PwrCommand(await self._exec_cmd("pwr"))

    async def unit(self) -> UnitCommand:
        """Invoke the 'unit' console command."""
        return UnitCommand(await self._exec_cmd("unit"))
