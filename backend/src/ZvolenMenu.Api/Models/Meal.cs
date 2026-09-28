namespace ZvolenMenu.Api.Models;

public class Meal
{
    public int Id { get; set; }
    public int DailyMenuId { get; set; }
    public int MenuTypeId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public decimal Price { get; set; }
    public string? Allergens { get; set; }
    public int SortOrder { get; set; }

    public DailyMenu DailyMenu { get; set; } = null!;
    public MenuType MenuType { get; set; } = null!;
}
