namespace ZvolenMenu.Api.Models;

public class DailyMenu
{
    public int Id { get; set; }
    public int RestaurantId { get; set; }
    public DateOnly MenuDate { get; set; }
    public string? Note { get; set; }

    public Restaurant Restaurant { get; set; } = null!;
    public ICollection<Meal> Items { get; set; } = new List<Meal>();
}
