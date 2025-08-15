use pyo3::prelude::*;
use std::fs;

#[pyfunction]
fn read_file(path: &str) -> PyResult<String> {
    let content = fs::read_to_string(path)?;
    Ok(content)
}

#[pyfunction]
fn write_file(path: &str, content: &str) -> PyResult<()> {
    fs::write(path, content)?;
    Ok(())
}

#[pymodule]
fn fsops_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(read_file, m)?)?;
    m.add_function(wrap_pyfunction!(write_file, m)?)?;
    Ok(())
}
