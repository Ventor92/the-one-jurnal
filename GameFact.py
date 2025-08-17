from typing import List, Literal, Optional, Mapping
import json

from pydantic import BaseModel, Field

class GameFact(BaseModel):
    typ: Literal["npc", "lokacja", "wydarzenie", "przedmiot"] = Field(
        ..., description="Kategoria elementu gry"
    )
    nazwa: str = Field(..., description="Nazwa elementu gry")
    opis: str = Field(..., description="Opis elementu")
    tagi: list[str] = Field(default_factory=list, description="Lista tagów pomocniczych")
    data_w_grze: Optional[str] = Field(None, description="Data w świecie gry (opcjonalna)")
    sesja: Optional[int] = Field(None, description="Numer sesji, w której wystąpił element")
    powiązania: list[str] = Field(default_factory=list, description="Powiązania z innymi elementami")
    log: str = Field(..., description="Oryginalny fragment transkrypcji, w którym pojawia się ten element")

    def to_metadata(self) -> Mapping:
        """Zwraca metadane jako Mapping zgodny z typem Metadata."""
        return {
            "typ": self.typ,
            "nazwa": self.nazwa,
            "opis": self.opis,
            "data_w_grze": self.data_w_grze,
            "sesja": self.sesja,
            "log": self.log,
            "tagi": json.dumps(self.tagi) if self.tagi else None,
            "powiązania": json.dumps(self.powiązania) if self.powiązania else None,
        }

    @classmethod
    def from_metadata(cls, metadata: Mapping) -> "GameFact":
        """Odtwarza GameFact z Mapping (deserializacja JSON-owych list)."""
        return cls(
            typ=metadata["typ"],
            nazwa=metadata["nazwa"],
            opis=metadata["opis"],
            data_w_grze=metadata.get("data_w_grze"),
            sesja=metadata.get("sesja"),
            log=metadata["log"],
            tagi=json.loads(metadata["tagi"]) if metadata.get("tagi") else [],
            powiązania=json.loads(metadata["powiązania"]) if metadata.get("powiązania") else [],
        )
    
    def __str__(self):
        """Zwraca czytelną reprezentację obiektu."""
        return f"{self.typ.capitalize()} '{self.nazwa}': {self.opis} (Data: {self.data_w_grze}, Sesja: {self.sesja})"
    
    def __repr__(self):
        """Zwraca reprezentację obiektu do debugowania."""
        return f"GameFact(typ={self.typ}, nazwa={self.nazwa}, opis={self.opis}, data_w_grze={self.data_w_grze}, sesja={self.sesja})"