use std::io;
use leetcode_hero::math::operations;

fn main() {
    show("Welcome to leetcode hero");
    show("Use: add, subtract, multiply, divide");
    let mut op = a_str();
    let op = process_string(&mut op);

}

pub fn a_str() -> String {
    String::new()
}

pub fn process_string(input: &mut str) -> String {
    io::stdin().read_line(input).unwrap();
    input.trim().to_string()
}

pub fn cli() {
    todo!()
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
