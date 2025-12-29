using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class User
    {
        public Guid Id { get; set; } = Guid.NewGuid();

        // Profile Information
        public string? FirstName { get; set; }
        public string? LastName { get; set; }
        public string Email { get; set; }
        public string DialCode { get; set; }
        public string PhoneNumber { get; set; }
        public UserStatus UserStatus { get; set; } = UserStatus.Active;
        public UserType UserType { get; set; } = UserType.Admin;
        public bool IsPhoneVerified { get; set; }
        public bool IsEmailVerified { get; set; }
        public bool IsEkeysSingnUp { get; set; }
        public string? AddressLine1 { get; set; }

        public virtual Country? Country { get; set; }
        public Guid? CountryId { get; set; }

        public string? State { get; set; }
        public string? City { get; set; }
        public string? ZipCode { get; set; }

        // Authentication
        public string? TTLockUsername { get; set; }
        public string? TTLockHashPassword { get; set; }

        public string? PasswordHash { get; set; }   // store hashed password
        public string? PasswordSalt { get; set; }   // optional, if using salted hashing
       
        // Login/Account Management
        public bool IsActive { get; set; } = true;
        public int FailedLoginAttempts { get; set; } = 0;
        public DateTime? LastLogin { get; set; }

        // Audit Fields
        public DateTime CreatedAt { get; set; } =DateTimeHelper.GetUtcTime();
        public DateTime UpdatedAt { get; set; } = DateTimeHelper.GetUtcTime();
        public List<AccessRefreshToken>? AccessRefreshToken { get; set; } = new();
        public List<UserParameter>? UserParameter { get; set; } = new();
        public string FullName
        {
            get { return $"{FirstName} {LastName}"; }
        }
    }
    public enum UserType
    {
        User,
        Admin,
    }
    public enum UserStatus
    {
        Active,
        DisabledByAdmin,
        Deleted
    }

}
