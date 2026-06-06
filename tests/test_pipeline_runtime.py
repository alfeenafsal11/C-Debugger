from src.pipeline.pipeline import DebuggingPipeline

pipeline = DebuggingPipeline()

code = """
#include <iostream>

int main() {
    int* ptr = nullptr;
    std::cout << *ptr;
}
"""

result = pipeline.run(code)

print(result)