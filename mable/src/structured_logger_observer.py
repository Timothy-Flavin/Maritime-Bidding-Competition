# src/observers/structured_logger_observer.py

import os
import json
import pandas as pd
from mable.observers import EventObserver

class StructuredLoggerObserver(EventObserver):
    def __init__(self, output_dir="logs", file_name="structured_events.json"):
        self.events = []
        self.output_dir = output_dir
        self.file_name = file_name

    def notify(self, engine, event, data):
        event_type = type(event).__name__

        if event_type in {"CargoTransferEvent", "TravelEvent", "AuctionCargoEvent", "TimeWindowArrivalEvent"}:
            record = {
                "timestamp": event.time,
                "event_type": event_type,
            }

            info = getattr(event, 'info', None)

            if hasattr(info, '__dict__'):
                record.update({
                    "vessel_name": getattr(info, 'vessel', None).name if getattr(info, 'vessel', None) else None,
                    "origin_port": getattr(info, 'origin_port', None).name if getattr(info, 'origin_port', None) else None,
                    "destination_port": getattr(info, 'destination_port', None).name if getattr(info, 'destination_port', None) else None,
                    "cargo_type": getattr(info, 'cargo_type', None),
                    "amount": getattr(info, 'amount', None),
                    "fuel_consumption": getattr(info, 'fuel_consumption', None),
                    "co2_emissions": getattr(info, 'co2_emissions', None),
                    "cost": getattr(info, 'cost', None),
                    "trade_payment": getattr(info, 'payment', None),
                })

            self.events.append(record)

    def get_dataframe(self):
        return pd.DataFrame(self.events)

    def save(self):
        os.makedirs(self.output_dir, exist_ok=True)
        path = os.path.join(self.output_dir, self.file_name)
        with open(path, "w") as f:
            json.dump(self.events, f, indent=2)
