using Resido.Helper;

namespace Resido.Database.DBTable
{
    public class PinCode
    {
        public Guid Id { get; set; }

        // Corresponding int ID from device / lock
        public int KeyboardPwdId { get; set; }

        public string? Pin { get; set; }

        public Guid SmartLockId { get; set; }
        public virtual SmartLock SmartLock { get; set; }

        public DateTime CreatedAt { get; set; }= DateTimeHelper.GetUtcTime();

        public DateTime? UpdatedAt { get; set; }
    }
}
