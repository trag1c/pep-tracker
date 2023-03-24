use std::collections::HashMap;
use std::fs;
use std::ops::{BitXor, Index};

use lazy_static::lazy_static;
use serde_json::json;

lazy_static! {
    pub static ref COLOR_CODES: HashMap<&'static str, &'static str> = {
        let mut dict = HashMap::new();
        dict.insert("Accepted", "&2");
        dict.insert("Active", "&a");
        dict.insert("Deferred", "&6");
        dict.insert("Draft", "&8");
        dict.insert("Final", "&1");
        dict.insert("Provisional", "&5");
        dict.insert("Rejected", "&4");
        dict.insert("Replaced", "&e");
        dict.insert("Withdrawn", "&d");
        dict
    };
}

const CACHE_PATH: &'static str = "pep-tracker/cache.json";
const URL: &'static str = "https://peps.python.org/api/peps.json";

#[derive(Debug, Clone, PartialEq)]
struct Cache {
    _data: HashMap<String, String>,
    datetime: chrono::DateTime<chrono::Utc>,
}

impl Cache {
    fn new(
        data: HashMap<String, String>,
        registered_at: Option<chrono::DateTime<chrono::Utc>>,
    ) -> Cache {
        Cache {
            _data: data,
            datetime: registered_at.unwrap_or(chrono::Utc::now()),
        }
    }
    fn dump(&self) -> String {
        json!(self._data).to_string()
    }
}

impl Index<String> for Cache {
    type Output = String;

    fn index(&self, index: String) -> &Self::Output {
        &self._data[&index]
    }
}

impl BitXor for Cache {
    type Output = HashMap<String, String>;

    fn bitxor(self, rhs: Self) -> Self::Output {
        let mut diff = HashMap::<String, String>::new();
        for (key, value) in self._data {
            if value != rhs[key.clone()] {
                diff.insert(key.clone(), value);
            }
        }
        diff
    }
}

fn get_current_state() -> Result<reqwest::blocking::Response, reqwest::Error> {
    reqwest::blocking::get(URL)?.error_for_status()
}

fn cache_current_state() {
    match get_current_state() {
        Ok(res) => {
            fs::write(CACHE_PATH, res.text().expect("invalid request body"));
        }
        Err(e) => {
            todo!();
        }
    }
}

fn main() {
    todo!();
}
