# Copyright (c) Microsoft. All rights reserved.
# Licensed under the MIT license. See LICENSE file in the project root for
# full license information.
from dictionary_object import DictionaryObject, SimpleObject, string_to_timedelta
import pytest
import datetime

fake_dict_integer_value = 42
fake_dict_float_value = 42.42
fake_dict_string_value = "fourty-two"
fake_dict_boolean_value = True
fake_dict_none_value = None
fake_dict_timedelta_value = datetime.timedelta(hours=2)
fake_dict_datetime_value = datetime.datetime(
    year=1984, month=12, day=31, hour=14, minute=32, second=17
)

fake_sub_integer_value = 52
fake_sub_float_value = 52.52
fake_sub_string_value = "fifty-two"
fake_sub_boolean_value = False
fake_sub_none_value = None
fake_sub_timedelta_value = datetime.timedelta(hours=12)
fake_sub_datetime_value = datetime.datetime(
    year=1994, month=11, day=30, hour=13, minute=12, second=12
)

fake_sub_sub_value = 62


class FakeSubObject(SimpleObject):
    def __init__(self):
        super(FakeSubObject, self).__init__()
        self.sub_integer_value = None
        self.sub_float_value = None
        self.sub_string_value = None
        self.sub_boolean_value = None
        self.sub_none_value = None
        self.sub_timedelta_value = datetime.timedelta(0)
        self.sub_datetime_value = datetime.datetime.min

    def populate(self):
        self.sub_integer_value = fake_sub_integer_value
        self.sub_float_value = fake_sub_float_value
        self.sub_string_value = fake_sub_string_value
        self.sub_boolean_value = fake_sub_boolean_value
        self.sub_none_value = fake_sub_none_value
        self.sub_timedelta_value = fake_sub_timedelta_value
        self.sub_datetime_value = fake_sub_datetime_value


class FakeDictionaryObject(DictionaryObject):
    def __init__(self):
        super(FakeDictionaryObject, self).__init__()
        self.sub_object = FakeSubObject()
        self.dict_integer_value = None
        self.dict_float_value = None
        self.dict_string_value = None
        self.dict_boolean_value = None
        self.dict_none_value = None
        self.dict_timedelta_value = datetime.timedelta(0)
        self.dict_datetime_value = datetime.datetime.min

    def populate(self):
        self.sub_object.populate()
        self.dict_integer_value = fake_dict_integer_value
        self.dict_float_value = fake_dict_float_value
        self.dict_string_value = fake_dict_string_value
        self.dict_boolean_value = fake_dict_boolean_value
        self.dict_none_value = fake_dict_none_value
        self.dict_timedelta_value = fake_dict_timedelta_value
        self.dict_datetime_value = fake_dict_datetime_value


@pytest.mark.describe("DictionaryObject to_dict method")
class TestDictionaryObjectToDict(object):
    @pytest.fixture
    def native_object(self):
        obj = FakeDictionaryObject()
        obj.populate()
        return obj

    @pytest.fixture
    def native_object_defaults(self):
        obj = FakeDictionaryObject()
        obj.populate()
        return obj

    @pytest.fixture
    def remove_nones_for_diff_test(self, native_object):
        # most diff tests ignore objects with value None.
        # since None is special in json patches, it's special here, so
        # we remove it for most diff tests
        del native_object.dict_none_value
        del native_object.sub_object.sub_none_value

    @pytest.fixture
    def add_sub_sub(self, native_object, native_object_defaults):
        native_object.sub_object.sub_sub_object = SimpleObject()
        native_object.sub_object.sub_sub_object.sub_sub_value = fake_sub_sub_value

        native_object_defaults.sub_object.sub_sub_object = SimpleObject()
        native_object_defaults.sub_object.sub_sub_object.sub_sub_value = (
            fake_sub_sub_value
        )

    @pytest.mark.it("returns a dictionary object")
    def test_returns_dict(self, native_object):
        d = DictionaryObject.to_dict(native_object)
        assert isinstance(d, dict)

    @pytest.mark.it("serializes scalar values in the root object")
    def test_serializes_root_scalars(self, native_object):
        d = DictionaryObject.to_dict(native_object)

        assert d["dictIntegerValue"] == fake_dict_integer_value
        assert d["dictFloatValue"] == fake_dict_float_value
        assert d["dictStringValue"] == fake_dict_string_value
        assert d["dictBooleanValue"] == fake_dict_boolean_value
        assert d["dictNoneValue"] == fake_dict_none_value
        assert d["dictTimedeltaValue"] == str(fake_dict_timedelta_value)
        assert d["dictDatetimeValue"] == str(fake_dict_datetime_value)

    @pytest.mark.it("serializes scalar values in sub objects")
    def test_serializes_sub_scalars(self, native_object):
        d = DictionaryObject.to_dict(native_object)

        assert d["subObject"]["subIntegerValue"] == fake_sub_integer_value
        assert d["subObject"]["subFloatValue"] == fake_sub_float_value
        assert d["subObject"]["subStringValue"] == fake_sub_string_value
        assert d["subObject"]["subBooleanValue"] == fake_sub_boolean_value
        assert d["subObject"]["subNoneValue"] == fake_sub_none_value
        assert d["subObject"]["subTimedeltaValue"] == str(fake_sub_timedelta_value)
        assert d["subObject"]["subDatetimeValue"] == str(fake_sub_datetime_value)

    @pytest.mark.it("recurses past the second level")
    def test_recurses(self, native_object):

        native_object.sub_object.sub = SimpleObject()
        native_object.sub_object.sub.level = 1
        native_object.sub_object.sub.sub = SimpleObject()
        native_object.sub_object.sub.sub.level = 2
        native_object.sub_object.sub.sub.sub = SimpleObject()
        native_object.sub_object.sub.sub.sub.level = 3
        native_object.sub_object.sub.sub.sub.sub = SimpleObject()
        native_object.sub_object.sub.sub.sub.sub.level = 3

        d = DictionaryObject.to_dict(native_object)

        assert isinstance(d["subObject"]["sub"], dict)
        assert d["subObject"]["sub"]["level"] == 1
        assert isinstance(d["subObject"]["sub"]["sub"], dict)
        assert d["subObject"]["sub"]["sub"]["level"] == 2
        assert isinstance(d["subObject"]["sub"]["sub"]["sub"], dict)
        assert d["subObject"]["sub"]["sub"]["sub"]["level"] == 3

    @pytest.mark.it("returns an empty object if all attribute values are default")
    def test_returns_empty_object_for_all_defaults(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        d = native_object.to_dict(native_object_defaults)
        assert d == {}

    @pytest.mark.it(
        "only includes attributes in the root that have changed from the default"
    )
    def test_only_includes_changed_values_in_the_root(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.dict_integer_value = 100
        d = native_object.to_dict(native_object_defaults)
        assert d == {"dictIntegerValue": 100}

    @pytest.mark.it(
        "only includes attributes in sub-objects that have changed from the default"
    )
    def test_only_includes_changed_values_in_sub_objects(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.sub_object.sub_integer_value = 100
        d = native_object.to_dict(native_object_defaults)
        assert d == {"subObject": {"subIntegerValue": 100}}

    @pytest.mark.it("does not include sub-objects if all their values are default")
    def test_does_not_include_sub_objects_with_no_changes(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.dict_integer_value = 100
        d = native_object.to_dict(native_object_defaults)
        assert d == {"dictIntegerValue": 100}

    @pytest.mark.it(
        "does include sub-objects if they have sub-sub-objects with non-default values"
    )
    def test_does_include_sub_objects_with_changed_sub_sub_objects(
        self,
        native_object,
        native_object_defaults,
        remove_nones_for_diff_test,
        add_sub_sub,
    ):
        native_object.sub_object.sub_sub_object.sub_sub_value = 200
        d = native_object.to_dict(native_object_defaults)
        assert d == {"subObject": {"subSubObject": {"subSubValue": 200}}}

    @pytest.mark.it("always includes values in the root with no default")
    def test_always_includes_new_values_in_root(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.new_value = 300
        d = native_object.to_dict(native_object_defaults)
        assert d == {"newValue": 300}

    @pytest.mark.it("always includes values in sub objects with no default")
    def test_always_incldues_new_values_in_sub_object(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.sub_object.new_sub_value = 400
        d = native_object.to_dict(native_object_defaults)
        assert d == {"subObject": {"newSubValue": 400}}

    @pytest.mark.it(
        "always includes entire sub-object if there is no default for the sub-object"
    )
    def test_includes_new_sub_objects_with_no_default(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.new_sub = SimpleObject()
        native_object.new_sub.first_value = 1
        native_object.new_sub.second_value = 2
        d = native_object.to_dict(native_object_defaults)
        assert d == {"newSub": {"firstValue": 1, "secondValue": 2}}

    @pytest.mark.it(
        "always include None in the root object even if the default is None"
    )
    def test_always_includes_none_in_root_object(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.dict_none_value = None
        assert native_object_defaults.dict_none_value is None
        d = native_object.to_dict(native_object_defaults)
        assert d == {"dictNoneValue": None}

    @pytest.mark.it("always include None in sub objects even if the default is None")
    def test_always_includes_none_in_sub_objects(
        self, native_object, native_object_defaults, remove_nones_for_diff_test
    ):
        native_object.sub_object.sub_none_value = None
        assert native_object_defaults.sub_object.sub_none_value is None
        d = native_object.to_dict(native_object_defaults)
        assert d == {"subObject": {"subNoneValue": None}}


@pytest.mark.describe("DictionaryObject from_dict method")
class TestDictionaryObjectFromDict(object):
    @pytest.fixture
    def dict_object(self):
        return {
            "dictIntegerValue": fake_dict_integer_value,
            "dictFloatValue": fake_dict_float_value,
            "dictStringValue": fake_dict_string_value,
            "dictBooleanValue": fake_dict_boolean_value,
            "dictNoneValue": fake_dict_none_value,
            "dictTimedeltaValue": str(fake_dict_timedelta_value),
            "dictDatetimeValue": str(fake_dict_datetime_value),
            "subObject": {
                "subIntegerValue": fake_sub_integer_value,
                "subFloatValue": fake_sub_float_value,
                "subStringValue": fake_sub_string_value,
                "subBooleanValue": fake_sub_boolean_value,
                "subNoneValue": fake_sub_none_value,
                "subTimedeltaValue": str(fake_sub_timedelta_value),
                "subDatetimeValue": str(fake_sub_datetime_value),
            },
        }

    @pytest.mark.it("Returns an object of the type of the class it was invoked from")
    def test_returns_correct_type(self, dict_object):
        obj = FakeDictionaryObject.from_dict(dict_object)

        assert type(obj) == FakeDictionaryObject
        assert type(obj.sub_object) == FakeSubObject

    @pytest.mark.it(
        "Sets existing scalar attributes on the returned object from scalar dictionary values"
    )
    def test_sets_existing_scalar_attribute(self, dict_object):
        obj = FakeDictionaryObject.from_dict(dict_object)

        assert obj.dict_integer_value == fake_dict_integer_value
        assert obj.dict_float_value == fake_dict_float_value
        assert obj.dict_string_value == fake_dict_string_value
        assert obj.dict_boolean_value == fake_dict_boolean_value
        assert obj.dict_none_value == fake_dict_none_value

    @pytest.mark.it(
        "Creates new scalar attributes on the returned object from scalar dictionary values"
    )
    def test_sets_new_scalar_attribute(self, dict_object):

        dict_object["newDictIntegerValue"] = fake_dict_integer_value
        dict_object["newDictFloatValue"] = fake_dict_float_value
        dict_object["newDictStringValue"] = fake_dict_string_value
        dict_object["newDictBooleanValue"] = fake_dict_boolean_value
        dict_object["newDictNoneValue"] = fake_dict_none_value

        obj = FakeDictionaryObject.from_dict(dict_object)

        assert obj.new_dict_integer_value == fake_dict_integer_value
        assert obj.new_dict_float_value == fake_dict_float_value
        assert obj.new_dict_string_value == fake_dict_string_value
        assert obj.new_dict_boolean_value == fake_dict_boolean_value
        assert obj.new_dict_none_value == fake_dict_none_value

    @pytest.mark.it(
        "Fills existing object attributes on the returned object from sub-dictionary values"
    )
    def test_sets_existing_sub_object_attributes(self, dict_object):
        obj = FakeDictionaryObject.from_dict(dict_object)

        assert obj.sub_object.sub_integer_value == fake_sub_integer_value
        assert obj.sub_object.sub_float_value == fake_sub_float_value
        assert obj.sub_object.sub_string_value == fake_sub_string_value
        assert obj.sub_object.sub_boolean_value == fake_sub_boolean_value
        assert obj.sub_object.sub_none_value == fake_sub_none_value

    @pytest.mark.it(
        "Creates new object attributes on the returned object from sub-dictionary values"
    )
    def test_creates_and_fills_new_sub_object_attributes(self, dict_object):

        dict_object["newSubObject"] = {}
        dict_object["newSubObject"]["subIntegerValue"] = fake_sub_integer_value
        dict_object["newSubObject"]["subFloatValue"] = fake_sub_float_value
        dict_object["newSubObject"]["subStringValue"] = fake_sub_string_value
        dict_object["newSubObject"]["subBooleanValue"] = fake_sub_boolean_value
        dict_object["newSubObject"]["subNoneValue"] = fake_sub_none_value

        obj = FakeDictionaryObject.from_dict(dict_object)

        assert type(obj.new_sub_object) == SimpleObject
        assert obj.new_sub_object.sub_integer_value == fake_sub_integer_value
        assert obj.new_sub_object.sub_float_value == fake_sub_float_value
        assert obj.new_sub_object.sub_string_value == fake_sub_string_value
        assert obj.new_sub_object.sub_boolean_value == fake_sub_boolean_value
        assert obj.new_sub_object.sub_none_value == fake_sub_none_value

    @pytest.mark.it("Recurses into mew sub_objects")
    def test_recurses_into_mew_sub_objects(self, dict_object):
        dict_object["subObject"]["sub"] = {
            "level": 1,
            "sub": {"level": 2, "sub": {"level": 3}},
        }

        obj = FakeDictionaryObject.from_dict(dict_object)

        assert type(obj.sub_object.sub) == SimpleObject
        assert obj.sub_object.sub.level == 1
        assert type(obj.sub_object.sub.sub) == SimpleObject
        assert obj.sub_object.sub.sub.level == 2
        assert type(obj.sub_object.sub.sub.sub) == SimpleObject
        assert obj.sub_object.sub.sub.sub.level == 3

    @pytest.mark.it(
        "converts datetime and timedelta values according to the destination type"
    )
    def test_converts_values_according_to_destination_type(self, dict_object):
        obj = FakeDictionaryObject.from_dict(dict_object)
        assert type(obj.dict_datetime_value) == datetime.datetime
        assert type(obj.dict_timedelta_value) == datetime.timedelta
        assert type(obj.sub_object.sub_datetime_value) == datetime.datetime
        assert type(obj.sub_object.sub_timedelta_value) == datetime.timedelta


class TestStringToTimedelta(object):
    @pytest.mark.parametrize(
        "s",
        [
            "3:00:00",
            "12:00:00",
            "23:59:59",
            "1157 days, 9:46:39",
            "12:00:01.824952",
            "-1 day, 23:59:31.859767",
        ],
    )
    def tests_converts_correctly(self, s):
        td = string_to_timedelta(s)
        assert str(td) == s


@pytest.mark.describe("lock_attributes method")
class TestLockAttributes(object):
    @pytest.fixture
    def three_level_object(self):
        obj = FakeDictionaryObject()
        obj.sub_object.sub_object = FakeSubObject()
        return obj

    @pytest.mark.it(
        "Causes new attributes on this objec and all sub objects to raise exceptions"
    )
    def test_raises(self, three_level_object):
        three_level_object.lock_attributes()

        with pytest.raises(AttributeError):
            three_level_object.new_attr = 1

        with pytest.raises(AttributeError):
            three_level_object.sub_object.new_attr = 1

        with pytest.raises(AttributeError):
            three_level_object.sub_object.sub_object.new_attr = 1

    @pytest.mark.it(
        "Does not cause existing attributes on this objec and all sub objects to raise exceptions"
    )
    def test_does_not_raise(self, three_level_object):
        three_level_object.lock_attributes()
        three_level_object.dict_integer_value = 1
        three_level_object.sub_object.sub_integer_value = 1
        three_level_object.sub_object.sub_object.sub_integer_value = 1
