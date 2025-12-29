using Resido.Database.DBTable;
using Resido.Helper;

namespace Resido.BAL
{
    public class CommonLogic
    {
        public static void SetDefaultUserInfo(User user)
        {
            user.UserStatus = UserStatus.Active;
            user.CreatedAt = DateTimeHelper.GetUtcTime();
            user.UpdatedAt = DateTimeHelper.GetUtcTime();
        }
        public static string GenerateUserName(User user)
        {
            string ttlockUsername;
            var now = DateTime.UtcNow;
            string timeStamp = $"{now:HHmmss}"; // HourMinuteSecond for uniqueness

            if (!string.IsNullOrWhiteSpace(user.Email))
            {
                // Take part before '@' in email
                var atIndex = user.Email.IndexOf('@');
                var baseName = atIndex > 0 ? user.Email.Substring(0, atIndex) : user.Email;

                // Remove invalid chars (keep only letters and digits)
                var cleanName = new string(baseName
                    .Where(ch => char.IsLetterOrDigit(ch))
                    .ToArray());

                // Ensure not empty and append timestamp
                ttlockUsername = string.IsNullOrWhiteSpace(cleanName)
                    ? $"user{DateTimeOffset.UtcNow.ToUnixTimeSeconds()}{Random.Shared.Next(100, 999)}"
                    : $"{cleanName}{timeStamp}";
            }
            else if (!string.IsNullOrWhiteSpace(user.PhoneNumber))
            {
                // Use phone number (ignore dial code) and append timestamp
                var cleanPhone = user.PhoneNumber.Replace("+", "").Replace(" ", "");
                ttlockUsername = $"{cleanPhone}{timeStamp}";
            }
            else
            {
                // Fallback: generic user + timestamp + random
                ttlockUsername = $"user{DateTimeOffset.UtcNow.ToUnixTimeSeconds()}{Random.Shared.Next(100, 999)}";
            }

            return ttlockUsername;
        }
        internal static string Generateneotp()
        {
            string sOTP = String.Empty;
            string sTempChars = String.Empty;
            Random rand = new Random();
            string[] saAllowedCharacters = { "1", "2", "3", "4", "5", "6", "7", "8", "9", "0" };
            for (int i = 0; i < 4; i++)
            {
                int p = rand.Next(0, saAllowedCharacters.Length);
                sTempChars = saAllowedCharacters[rand.Next(0, saAllowedCharacters.Length)];
                sOTP += sTempChars;
            }
            return sOTP;
            //return "1992";
        }
        #region ParameterOperation
        internal static string? GetUserParamValue(List<UserParameter>? userParameters, UserParameterKey userParameterKey)
        {
            if (userParameters != null && userParameters.Any(a => a.Key.ToLower() == userParameterKey.ToString().ToLower()))
            {
                return userParameters.FirstOrDefault(a => a.Key.ToLower() == userParameterKey.ToString().ToLower())?.Value;
            }
            return string.Empty;
        }
        internal static UserParameter? GetUserParamObject(List<UserParameter>? userParameters, UserParameterKey userParameterKey)
        {
            if (userParameters != null && userParameters.Any(a => a.Key.ToLower() == userParameterKey.ToString().ToLower()))
            {
                return userParameters.FirstOrDefault(a => a.Key.ToLower() == userParameterKey.ToString().ToLower());
            }
            return new UserParameter();
        }
        internal static bool CheckParamKeyExist(List<UserParameter>? userParameters, UserParameterKey userParameterKey)
        {
            if (userParameters != null && userParameters.Any(a => a.Key.ToLower() == userParameterKey.ToString().ToLower()))
            {
                return true;
            }
            else
            {
                return false;
            }
        }
        internal static UserParameter CreateUserParamObject(UserParameterKey userParameterKey, string value)
        {
            return new UserParameter
            {
                Key = userParameterKey.ToString().ToLower(),
                Value = value,
                CreatedAt = DateTime.UtcNow,
                UpdatedAt = DateTime.UtcNow,
                RowStatus = RowStatus.Active
            };
        }

        internal static List<UserParameter>? UpdateUserParameter(List<UserParameter>? userParameters, UserParameterKey userParameterKey, string value)
        {
            if (userParameters?.Any() ?? false)
            {
                var userParameter = userParameters.FirstOrDefault(x => x.Key == userParameterKey.ToString().ToLower());
                if (userParameter != null)
                {
                    userParameter.Value = value;
                }
                ;
            }
            return userParameters;
        }
        internal static List<UserParameter>? DeleteUserParameter(List<UserParameter>? userParameters, UserParameterKey userParameterKey)
        {
            if (userParameters?.Any() ?? false)
            {
                var userParameter = userParameters.FirstOrDefault(x => x.Key == userParameterKey.ToString().ToLower());
                if (userParameter != null)
                {
                    userParameters.Remove(userParameter);
                }
                ;
            }
            return userParameters;
        }
        public static List<UserParameter> UpsertUserParameter(
    List<UserParameter> parameters,
    UserParameterKey key,
    string value)
        {
            if (parameters == null)
                parameters = new List<UserParameter>();

            var existingParam = parameters.FirstOrDefault(p => p.Key == key.ToLowerString());
            if (existingParam != null)
            {
                // Update existing value
                existingParam.Value = value;
                existingParam.UpdatedAt = DateTimeHelper.GetUtcTime();
            }
            else
            {
                // Insert new parameter
                parameters.Add(new UserParameter
                {
                    Key = key.ToLowerString(),
                    Value = value,
                    CreatedAt = DateTimeHelper.GetUtcTime(),
                    UpdatedAt = DateTimeHelper.GetUtcTime()
                });
            }

            return parameters;
        }

        #endregion

    }
}
