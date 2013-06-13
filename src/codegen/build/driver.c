#include <stdio.h>
#include <string.h>

extern void llvm_main();

char* io_in(char* buff, size_t len) {
  if (fgets(buff, len, stdin) != 0) {
    size_t len = strlen(buff);
    if (len > 0 && buff[len-1] == '\n')
      buff[len-1] = '\0';

    return buff;
  }
  return 0;
}

void io_out(char* out) {
  printf("%s", out);
}

int main() {
  llvm_main();
  return 0;
}
