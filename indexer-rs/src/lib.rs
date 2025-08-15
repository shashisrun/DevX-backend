use pyo3::prelude::*;
use walkdir::WalkDir;

#[pyfunction]
fn build_index(path: &str) -> PyResult<Vec<String>> {
    let mut files = Vec::new();
    for entry in WalkDir::new(path) {
        match entry {
            Ok(entry) => {
                if entry.file_type().is_file() {
                    files.push(entry.path().display().to_string());
                }
            }
            Err(e) => {
                return Err(pyo3::exceptions::PyRuntimeError::new_err(format!("WalkDir error: {}", e)));
            }
        }
    }
    Ok(files)
}

#[pyfunction]
fn search_index(query: &str) -> PyResult<Vec<String>> {
    // Dummy implementation
    Ok(vec![query.to_string()])
}

#[pymodule]
fn indexer_rs(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(build_index, m)?)?;
    m.add_function(wrap_pyfunction!(search_index, m)?)?;
    Ok(())
}
