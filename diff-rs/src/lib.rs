use pyo3::prelude::*;
use diff::lines;

#[pyfunction]
fn compute_diff(a: &str, b: &str) -> PyResult<Vec<String>> {
    let mut result = Vec::new();
    for diff in lines(a, b) {
        result.push(format!("{:?}", diff));
    }
    Ok(result)
}

#[pymodule]
fn diff_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(compute_diff, m)?)?;
    Ok(())
}
