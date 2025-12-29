use std::io;
use crate::math::operations;

pub fn cli() {
}

pub fn show(msg: &str) {
    println!("{}", msg);
}

pub fn get_input() -> String {
    let mut input = String::new();
    io::stdin()
        .read_line(&mut input).unwrap();
    let input = input.trim();
    input.to_string()
}

pub fn get_input_int() -> i32 {
    let input = get_input();
    input.parse::<i32>().unwrap()
}

pub fn get_input_float() -> f64 {
    let input = get_input();
    input.parse::<f64>().unwrap()
}
