# There is no datafile generation for testblock, all results are shown on terminal itself

from ucheck import languagecheck

def test_language_detection():    
    test_cases = [
        {
            "name": "Python",
            "code": """
def hello_world():
    print("Hello, World!")
    return True

if __name__ == "__main__":
    hello_world()
""",
            "expected": "py"
        },
        {
            "name": "Java",
            "code": """
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""",
            "expected": "java"
        },
        {
            "name": "C++",
            "code": """
#include <iostream>
using namespace std;

int main() {
    cout << "Hello, World!" << endl;
    return 0;
}
""",
            "expected": "cpp"
        },
        {
            "name": "C",
            "code": """
#include <stdio.h>

int main() {
    printf("Hello, World!\\n");
    return 0;
}
""",
            "expected": "c"
        },
        {
            "name": "JavaScript",
            "code": """
function helloWorld() {
    console.log("Hello, World!");
}

const message = "Hello";
helloWorld();
""",
            "expected": "js"
        },
        {
            "name": "Empty string",
            "code": "",
            "expected": "unknown"
        }
    ]
    
    print("Testing Language Detection\\n" + "="*50)
    
    for test_case in test_cases:
        text = test_case["code"]
        expected = test_case["expected"]
        
        # Call the languagecheck function
        result = languagecheck(text=text)
        
        status = "✓ PASS" if result == expected else "✗ FAIL"
        print(f"{test_case['name']:<15} | Expected: {expected:<8} | Got: {result:<8} | {status}")
        
        if result != expected:
            print(f"  Code sample: {text[:50].replace(chr(10), ' ')}...")
    
    print("\\n" + "="*50)


if __name__ == "__main__":
    test_language_detection()