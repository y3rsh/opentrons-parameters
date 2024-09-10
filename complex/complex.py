from opentrons import protocol_api
from dataclasses import dataclass
from typing import List, Union


metadata = {"name": "complex", "author": "Josh McVey", "description": ""}
requirements = {
    "robotType": "Flex",
    "apiLevel": "2.20",
}

HEADERS = [
    "0_liq_class",
    "1_asp_rate",
    "2_dis_rate",
    "3_delay_mode",
    "4_asp_zoffset",
    "5_dis_zoffset",
    "6_blowout_zoffset",
    "7_prewet (Yes or No)?",
    "8_prewet_rep",
    "9_slow_withdrawl_asp (Yes or No)?",
    "10_postmix (Yes or No)?",
    "11_postmix_vol",
    "12_postmix_rep",
    "13_slow_withdrawl_dis (Yes or No)?",
    "14_blowout_mode",
    "15_touch_tip(Yes or No)?",
    "16_t_height",
    "17_air_gap (Yes or No)?",
]


header_mapping = {
    "0_liq_class": "liq_class",
    "1_asp_rate": "asp_rate",
    "2_dis_rate": "dis_rate",
    "3_delay_mode": "delay_mode",
    "4_asp_zoffset": "asp_zoffset",
    "5_dis_zoffset": "dis_zoffset",
    "6_blowout_zoffset": "blowout_zoffset",
    "7_prewet (Yes or No)?": "prewet",
    "8_prewet_rep": "prewet_rep",
    "9_slow_withdrawl_asp (Yes or No)?": "slow_withdrawl_asp",
    "10_postmix (Yes or No)?": "postmix",
    "11_postmix_vol": "postmix_vol",
    "12_postmix_rep": "postmix_rep",
    "13_slow_withdrawl_dis (Yes or No)?": "slow_withdrawl_dis",
    "14_blowout_mode": "blowout_mode",
    "15_touch_tip(Yes or No)?": "touch_tip",
    "16_t_height": "t_height",
    "17_air_gap (Yes or No)?": "air_gap",
}


@dataclass
class LiquidClassConfig:
    liq_class: str
    asp_rate: float
    dis_rate: float
    delay_mode: str
    asp_zoffset: float
    dis_zoffset: float
    blowout_zoffset: float
    prewet: str
    prewet_rep: int
    slow_withdrawl_asp: str
    postmix: str
    postmix_vol: float
    postmix_rep: int
    slow_withdrawl_dis: str
    blowout_mode: str
    touch_tip: str
    t_height: float
    air_gap: str

    def __str__(self):
        return (
            f"LiquidClassConfig(\n"
            f"  liq_class='{self.liq_class}',\n"
            f"  asp_rate={self.asp_rate},\n"
            f"  dis_rate={self.dis_rate},\n"
            f"  delay_mode='{self.delay_mode}',\n"
            f"  asp_zoffset={self.asp_zoffset},\n"
            f"  dis_zoffset={self.dis_zoffset},\n"
            f"  blowout_zoffset={self.blowout_zoffset},\n"
            f"  prewet='{self.prewet}',\n"
            f"  prewet_rep={self.prewet_rep},\n"
            f"  slow_withdrawl_asp='{self.slow_withdrawl_asp}',\n"
            f"  postmix='{self.postmix}',\n"
            f"  postmix_vol={self.postmix_vol},\n"
            f"  postmix_rep={self.postmix_rep},\n"
            f"  slow_withdrawl_dis='{self.slow_withdrawl_dis}',\n"
            f"  blowout_mode='{self.blowout_mode}',\n"
            f"  touch_tip='{self.touch_tip}',\n"
            f"  t_height={self.t_height},\n"
            f"  air_gap='{self.air_gap}'\n"
            f")"
        )


def validate_data_rows(data_rows):
    """Process each row of data. Fail fast on the first row missing fields or that has empty fields"""
    for index, row in enumerate(data_rows, start=1):
        if len(row) != len(HEADERS):
            error = f"There are missing fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
            raise ValueError(error)

        for value in row:
            if value is None or value.strip() == "":
                error = f"There are empty fields in data row: {index}, line {index+1} of the CSV. The row data is: {row}"
                raise ValueError(error)


def read_liquid_class_config_from_list(
    data: List[List[Union[str, int, float]]]
) -> List[LiquidClassConfig]:
    """This function reads a list of lists and returns a list of LiquidClassConfig objects"""

    # The first row of our data is the headers
    headers = data[0]
    assert headers == HEADERS, f"Expected headers: {HEADERS}, but got: {headers}"

    # Ignore the first row, as it is the headers
    data_rows = data[1:]

    validate_data_rows(data_rows)
    # Iterate over the rest of the rows and create LiquidClassConfig objects
    liquid_class_configs = []

    for row in data_rows:
        liquid_class_config = LiquidClassConfig(
            liq_class=str(row[0]),
            asp_rate=float(row[1]),
            dis_rate=float(row[2]),
            delay_mode=str(row[3]),
            asp_zoffset=float(row[4]),
            dis_zoffset=float(row[5]),
            blowout_zoffset=float(row[6]),
            prewet=str(row[7]),
            prewet_rep=int(row[8]),
            slow_withdrawl_asp=str(row[9]),
            postmix=str(row[10]),
            postmix_vol=float(row[11]),
            postmix_rep=int(row[12]),
            slow_withdrawl_dis=str(row[13]),
            blowout_mode=str(row[14]),
            touch_tip=str(row[15]),
            t_height=float(row[16]),
            air_gap=str(row[17]),
        )
        liquid_class_configs.append(liquid_class_config)

    return liquid_class_configs


def add_parameters(parameters):
    parameters.add_csv_file(
        variable_name="liquid_class_configs",
        display_name="Liquid Class Configs",
        description="Table of liquid class configurations.",
    )


def run(protocol: protocol_api.ProtocolContext):
    # Read the liquid class config data
    liquid_class_config_csv = protocol.params.liquid_class_configs.parse_as_csv()
    liquid_class_config_data = read_liquid_class_config_from_list(
        liquid_class_config_csv
    )
    # Iterate over the liquid class configs and print them
    for liquid_class_config in liquid_class_config_data:
        protocol.comment(liquid_class_config.__str__())
