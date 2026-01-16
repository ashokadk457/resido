using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Model.TTLockDTO.ResponseDTO;
using Resido.Model.TTLockDTO.ResponseDTO.LockRsp;
using Resido.Resources;

namespace Resido.Services.DAL
{
    public class CommonDBLogic
    {
        ResidoDbContext _context;
        private readonly UserService _userService;
        private readonly IServiceScopeFactory _serviceScopeFactory;
        public CommonDBLogic(ResidoDbContext context, UserService userService, IServiceScopeFactory serviceScopeFactory)
        {
            _context = context;
            _userService = userService;
            _serviceScopeFactory = serviceScopeFactory;
        }
        internal async Task<Dictionary<Guid, SmartLockUsageCountDTO>> GetSmartLockUsageCountsAsync(List<Guid> smartLockIds)
        {
            var result = new Dictionary<Guid, SmartLockUsageCountDTO>();

            // Grouped counts (single DB hit per table)
            var pinCounts = await _context.PinCodes
                .Where(x => smartLockIds.Contains(x.SmartLockId))
                .GroupBy(x => x.SmartLockId)
                .Select(g => new { SmartLockId = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.SmartLockId, x => x.Count);

            var cardCounts = await _context.Cards
                .Where(x => smartLockIds.Contains(x.SmartLockId))
                .GroupBy(x => x.SmartLockId)
                .Select(g => new { SmartLockId = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.SmartLockId, x => x.Count);

            var fingerprintCounts = await _context.Fingerprints
                .Where(x => smartLockIds.Contains(x.SmartLockId))
                .GroupBy(x => x.SmartLockId)
                .Select(g => new { SmartLockId = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.SmartLockId, x => x.Count);

            var ekeyCounts = await _context.EKeys
                .Where(x => smartLockIds.Contains(x.SmartLockId))
                .GroupBy(x => x.SmartLockId)
                .Select(g => new { SmartLockId = g.Key, Count = g.Count() })
                .ToDictionaryAsync(x => x.SmartLockId, x => x.Count);

            foreach (var lockId in smartLockIds)
            {
                result[lockId] = new SmartLockUsageCountModel
                {
                    PinCodeCount = pinCounts.GetValueOrDefault(lockId),
                    PinCodeLimitCount = 250,

                    CardCount = cardCounts.GetValueOrDefault(lockId),
                    CardLimitCount = 1000,

                    FingerprintCount = fingerprintCounts.GetValueOrDefault(lockId),
                    FingerprintLimitCount = 100,

                    EkeyCount = ekeyCounts.GetValueOrDefault(lockId),
                    EkeyLimitCount = 500
                };
            }

            return result;
        }

        public void SaveAcccesAndRefreshToken(User user, AccessTokenResponseDTO token)
        {
            var access = _context.AccessRefreshTokens.FirstOrDefault(a => a.UserId == user.Id);
            if (access == null)
            {
                user.AccessRefreshToken ??= new List<AccessRefreshToken>();
                user.AccessRefreshToken.Add(new AccessRefreshToken(token)
                {
                    UserId = user.Id,
                });
            }

        }
        public async Task<(User?, LoginOtpDeliveryMethod, string?)> GetAndValidateUserAsync(string input, string? dialCode, bool checkDial = true)
        {
            var type = LoginOtpDeliveryMethod.Email;
            input = input.NormalizeInput();
            if (UserInputValidator.ValidateEmail(input, out string emailError))
            {
                return (await FindUserAsync(input), type, null);
            }

            if (UserInputValidator.ValidatePhoneNumber(input, out string phoneError))
            {
                if (checkDial && !UserInputValidator.ValidateDialCode(dialCode, out string errdialCode))
                    return (null, LoginOtpDeliveryMethod.Phone, errdialCode);

                type = LoginOtpDeliveryMethod.Phone;
                return (await FindUserAsync(input), type, null);
            }

            return (null, type, Resource.InvalidPhoneEmail);
        }
        public async Task<User?> FindUserAsync(string input)
           => await _context.Users.Include(a => a.UserParameter).FirstOrDefaultAsync(u => (!string.IsNullOrEmpty(u.Email) && u.Email.Trim().ToLower() == input) || u.PhoneNumber == input || u.TTLockUsername == input);

        // In CommonDBLogic or UserService
        public async Task<(bool isAvailable, string? error, User? user)> CheckEmailAvailabilityAsync(string email)
        {
            if (!UserInputValidator.ValidateEmail(email, out string emailError))
                return (false, emailError, null);

            var existingUser = await _userService.FindUserByEmailAsync(email);
            if (existingUser != null)
            {
                if (!existingUser.IsEmailVerified)
                    return (false, Resource.Email_NotVerified, existingUser);

                return (false, Resource.Email_AlreadyExists, existingUser);
            }

            return (true, null, null);
        }

        public async Task<(bool isAvailable, string? error, User? user)> CheckPhoneAvailabilityAsync(string phoneNumber, string? dialCode)
        {
            if (!UserInputValidator.ValidatePhoneNumber(phoneNumber, out string phoneError))
                return (false, phoneError, null);

            if (!UserInputValidator.ValidateDialCode(dialCode ?? string.Empty, out string dialError))
                return (false, dialError, null);

            var existingUser = await _userService.FindUserByPhoneAsync(phoneNumber, dialCode);
            if (existingUser != null)
            {
                if (!existingUser.IsPhoneVerified)
                    return (false, Resource.PhoneNumber_NotVerified, existingUser);

                return (false, Resource.PhoneNumber_AlreadyExists, existingUser);
            }

            return (true, null, null);
        }

    }
}
