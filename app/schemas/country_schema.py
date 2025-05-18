from pydantic import BaseModel, Field
from typing import Optional

class CountryUpdate(BaseModel):
    name: Optional[str] = Field(None, example="South Africa")
    population: Optional[int] = Field(None, example=59308690)
    capital: Optional[str] = Field(None, example="Pretoria")
    flag: Optional[str] = Field(None, example="https://flagcdn.com/w320/za.png")
    region: Optional[str] = Field(None, example="Africa")
    subregion: Optional[str] = Field(None, example="Southern Africa")
    languages: Optional[str] = Field(
        None,
        example="Afrikaans, English, Southern Ndebele, Northern Sotho, Southern Sotho, Swazi, Tswana, Tsonga, Venda, Xhosa, Zulu"
    )