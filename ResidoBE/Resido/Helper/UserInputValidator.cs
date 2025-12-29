using Resido.Resources;
using System.Text.RegularExpressions;

namespace Resido.Helper
{
    public class UserInputValidator
    {
        // -----------------------------
        // Individual reusable validators
        // -----------------------------

        public static bool ValidateEmail(string email, out string errorMessage)
        {
            errorMessage = string.Empty;

            if (string.IsNullOrWhiteSpace(email))
            {
                errorMessage = Resource.Email_Required;
                return false;
            }

            // Basic email format check
            if (!Regex.IsMatch(email, @"^[^@\s]+@[^@\s]+\.[^@\s]+$"))
            {
                errorMessage = Resource.Email_Invalid;
                return false;
            }

            return true;
        }

        public static bool ValidatePhoneNumber(string phoneNumber, out string errorMessage)
        {
            errorMessage = string.Empty;

            if (string.IsNullOrWhiteSpace(phoneNumber))
            {
                errorMessage = Resource.PhoneNumber_Required;
                return false;
            }

            if (!Regex.IsMatch(phoneNumber, @"^\d+$"))
            {
                errorMessage = Resource.PhoneNumber_Invalid;
                return false;
            }

            return true;
        }

        public static bool ValidateDialCode(string diaCode, out string errorMessage)
        {
            errorMessage = string.Empty;

            if (string.IsNullOrWhiteSpace(diaCode))
            {
                errorMessage = Resource.DialCode_Required;
                return false;
            }

            if (!Regex.IsMatch(diaCode, @"^\+\d{1,4}$"))
            {
                errorMessage = Resource.DialCode_Invalid;
                return false;
            }

            return true;
        }

        public static bool ValidatePassword(string password, out string errorMessage)
        {
            errorMessage = string.Empty;

            if (string.IsNullOrWhiteSpace(password))
            {
                errorMessage = Resource.Password_Required;
                return false;
            }

            // Password rules: min 6 chars, uppercase, digit, special char/space
            string pattern = @"^(?=.*[A-Z])(?=.*\d)(?=.*[-!@#$%^&*()_+ ])[\S\s]{6,}$";
            if (!Regex.IsMatch(password, pattern))
            {
                errorMessage = Resource.Password_Invalid;
                return false;
            }

            return true;
        }
    }

}
