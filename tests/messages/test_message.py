from aact.messages import DataModel, DataModelFactory


def test_create_data_model() -> None:
    # Create a new data model
    @DataModelFactory.register("MyDataModel")
    class MyDataModel(DataModel):
        name: str
        age: int

    # Create an instance of the data model
    instance = MyDataModel(name="John", age=30)

    # Validate the instance
    assert instance.name == "John"
    assert instance.age == 30

    # Check if the instance is of type DataModel
    assert isinstance(instance, DataModel)
