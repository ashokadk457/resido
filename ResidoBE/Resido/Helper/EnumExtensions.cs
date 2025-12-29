namespace Resido.Helper
{
    public static class EnumExtensions
    {
        /// <summary>
        /// Converts an enum value to a lowercase string.
        /// </summary>
        public static string ToLowerString(this Enum value)
        {
            return value.ToString().ToLowerInvariant();
        }
    }
}
