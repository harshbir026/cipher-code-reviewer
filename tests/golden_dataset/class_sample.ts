// Golden dataset: TS class/method for regression-testing the
// class_declaration `type_identifier` field (JS uses `identifier`).

class UserValidator {
  validateEmail(email: string): boolean {
    return email.includes("@");
  }
}