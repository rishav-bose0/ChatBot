from dataclasses import dataclass


@dataclass
class WebsiteDetails:
    websites: list[str]
    is_recursive: bool
