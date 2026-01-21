import yaml
from typing import Any


class TagKeyOf(yaml.YAMLObject):
    yaml_tag = "!KeyOf"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagFind(yaml.YAMLObject):
    yaml_tag = "!Find"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagFindObject(yaml.YAMLObject):
    yaml_tag = "!TagFindObject"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagContext(yaml.YAMLObject):
    yaml_tag = "!Context"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagFormat(yaml.YAMLObject):
    yaml_tag = "!Format"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagCondition(yaml.YAMLObject):
    yaml_tag = "!Condition"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagIf(yaml.YAMLObject):
    yaml_tag = "!If"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagEnv(yaml.YAMLObject):
    yaml_tag = "!Env"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagFile(yaml.YAMLObject):
    yaml_tag = "!File"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagEnumerate(yaml.YAMLObject):
    yaml_tag = "!Enumerate"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagValue(yaml.YAMLObject):
    yaml_tag = "!Value"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagIndex(yaml.YAMLObject):
    yaml_tag = "!Index"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagIndex(yaml.YAMLObject):
    yaml_tag = "!Index"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class TagAtIndex(yaml.YAMLObject):
    yaml_tag = "!AtIndex"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        if isinstance(data.value, list):
            return dumper.represent_sequence(cls.yaml_tag, data.value)
        return dumper.represent_mapping(cls.yaml_tag, data.value)


class TagParseJSON(yaml.YAMLObject):
    yaml_tag = "!ParseJSON"

    def __init__(self, value):
        self.value = value

    @classmethod
    def to_yaml(cls, dumper: yaml.SafeDumper, data):
        return dumper.represent_scalar(cls.yaml_tag, data.value)


class BlueprintDumper(yaml.SafeDumper):
    """Loader for blueprints with custom tag support"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.add_representer(TagKeyOf, TagKeyOf.to_yaml)
        self.add_representer(TagFind, TagFind.to_yaml)
        self.add_representer(TagFindObject, TagFindObject.to_yaml)
        self.add_representer(TagContext, TagContext.to_yaml)
        self.add_representer(TagFormat, TagFormat.to_yaml)
        self.add_representer(TagCondition, TagCondition.to_yaml)
        self.add_representer(TagIf, TagIf.to_yaml)
        self.add_representer(TagEnv, TagEnv.to_yaml)
        self.add_representer(TagFile, TagFile.to_yaml)
        self.add_representer(TagEnumerate, TagEnumerate.to_yaml)
        self.add_representer(TagValue, TagValue.to_yaml)
        self.add_representer(TagIndex, TagIndex.to_yaml)
        self.add_representer(TagAtIndex, TagAtIndex.to_yaml)
        self.add_representer(TagParseJSON, TagParseJSON.to_yaml)


def transpile_to_yaml_tags(data: Any) -> Any:
    """
    Recursively converts JSON-convention dicts into Tag Objects.
    """
    if isinstance(data, dict):
        if len(data) == 1:
            match list(data.keys())[0]:
                case "$KeyOf":
                    return TagKeyOf(data["$KeyOf"])
                case "$Find":
                    return TagFind(transpile_to_yaml_tags(data["$Find"]))
                case "$FindObject":
                    return TagFindObject(transpile_to_yaml_tags(data["$FindObject"]))
                case "$Context":
                    return TagContext(data["$Context"])
                case "$Format":
                    return TagFormat(transpile_to_yaml_tags(data["$Format"]))
                case "$Condition":
                    return TagCondition(transpile_to_yaml_tags(data["$Condition"]))
                case "$If":
                    return TagIf(transpile_to_yaml_tags(data["$If"]))
                case "$Env":
                    return TagEnv(data["$Env"])
                case "$File":
                    return TagFile(data["$File"])
                case "$Enumerate":
                    return TagEnumerate(transpile_to_yaml_tags(data["$Enumerate"]))
                case "$Value":
                    return TagValue(data["$Value"])
                case "$Index":
                    return TagIndex(data["$Index"])
                case "$AtIndex":
                    return TagAtIndex(data["$AtIndex"])
                case "$ParseJSON":
                    return TagParseJSON(data["$ParseJSON"])

        return {k: transpile_to_yaml_tags(v) for k, v in data.items()}

    elif isinstance(data, list):
        return [transpile_to_yaml_tags(item) for item in data]

    return data
