def test_package_version_importable():
    import edges_rag

    assert edges_rag.__version__ == "0.1.0"
