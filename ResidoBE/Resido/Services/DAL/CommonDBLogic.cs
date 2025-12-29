using Microsoft.EntityFrameworkCore;
using Resido.BAL;
using Resido.Database;
using Resido.Database.DBTable;
using Resido.Helper;
using Resido.Model.TTLockDTO.ResponseDTO;
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
