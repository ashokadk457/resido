namespace Resido.Helper
{
    public static class StringExtensions
    { /// <summary>
      /// Trims and converts the string to lowercase. Returns empty string if input is null.
      /// </summary>
        public static string NormalizeInput(this string input)
        {
            return input?.Trim().ToLower() ?? string.Empty;
        }
    }
}
