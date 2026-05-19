using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class AccessLog
    {
        public Guid Id { get; set; } = Guid.NewGuid();
        public int LockId { get; set; }
        public string? LockMac { get; set; }
        public int RecordType { get; set; }
        public int RecordTypeFromLock { get; set; }
        public string? RecordTypeDescription { get; set; }
        public string? Username { get; set; }
        public string? KeyboardPwd { get; set; }
        public DateTime LockDate { get; set; }  // Converted
        public int ElectricQuantity { get; set; }
        public int Success { get; set; }
        public long? RecordId { get; set; }
        public int? Uid { get; set; }
        public string? Password { get; set; }
        public string? NewPassword { get; set; }
        public DateTime ServerDate { get; set; } // Converted
        public DateTime CreatedAt { get; set; } = DateTimeHelper.GetUtcTime();

    }
}
