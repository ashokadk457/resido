using System.Security.Cryptography;
using System.Text;

namespace Resido.Helper
{
    public class PasswordHelper
    {

        private static readonly Random _random = new Random();
        private const string _chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";

        public static string GenerateRandomPassword(int length = 6)
        {
            char[] password = new char[length];
            for (int i = 0; i < length; i++)
            {
                password[i] = _chars[_random.Next(_chars.Length)];
            }
            return new string(password);
        }
        public static string ComputeSha256Ajax(string input)
        {
            using (SHA256 sha256 = SHA256.Create())
            {
                byte[] bytes = Encoding.UTF8.GetBytes(input);
                byte[] hash = sha256.ComputeHash(bytes);

                // Convert byte array to hex string
                StringBuilder result = new StringBuilder();
                foreach (byte b in hash)
                {
                    result.Append(b.ToString("x2")); // lowercase hex
                }
                return result.ToString();
            }
        }

        /// <summary>
        /// Generates a 32-character lowercase MD5 hash for TTLock API.
        /// </summary>
        public static string GenerateMd5ForTTLock(string plainPassword)
        {
            using (MD5 md5 = MD5.Create())
            {
                byte[] inputBytes = Encoding.UTF8.GetBytes(plainPassword);
                byte[] hashBytes = md5.ComputeHash(inputBytes);

                StringBuilder sb = new StringBuilder();
                foreach (var b in hashBytes)
                    sb.Append(b.ToString("x2")); // Lowercase hex format

                return sb.ToString(); // 32-character lowercase MD5
            }
        }
    }
}
