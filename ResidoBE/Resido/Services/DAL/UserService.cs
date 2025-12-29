using Microsoft.EntityFrameworkCore;
using Resido.Database;
using Resido.Database.DBTable;
using System;

namespace Resido.Services.DAL
{
    public class UserService
    {
        private readonly ResidoDbContext _context;

        public UserService(ResidoDbContext context)
        {
            _context = context;
        }

        /// <summary>
        /// Find a user by email (case-insensitive).
        /// </summary>
        public async Task<User?> FindUserByEmailAsync(string email)
        {
            if (string.IsNullOrWhiteSpace(email))
                return null;

            return await _context.Users
                .AsNoTracking()
                .FirstOrDefaultAsync(u => u.Email.ToLower() == email.ToLower());
        }

        /// <summary>
        /// Find a user by phone number and dial code.
        /// </summary>
        public async Task<User?> FindUserByPhoneAsync(string phoneNumber, string? dialCode)
        {
            if (string.IsNullOrWhiteSpace(phoneNumber) || string.IsNullOrWhiteSpace(dialCode))
                return null;

            return await _context.Users
                .AsNoTracking()
                .FirstOrDefaultAsync(u => u.PhoneNumber == phoneNumber && u.DialCode == dialCode);
        }
    }
}
