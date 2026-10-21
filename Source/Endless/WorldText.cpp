#include "WorldText.h"
#include "Components/WidgetComponent.h"
#include "Styling/CoreStyle.h"
#include "Widgets/Text/STextBlock.h"

namespace
{
	// The text is rendered at this many pixels per cm and scaled down, so letters stay sharp up close
	constexpr float PixelsPerCm = 4.f;
}

AWorldText::AWorldText()
{
	RootComponent = CreateDefaultSubobject<USceneComponent>(TEXT("Root"));

	Widget = CreateDefaultSubobject<UWidgetComponent>(TEXT("Widget"));
	Widget->SetupAttachment(RootComponent);
	Widget->SetWidgetSpace(EWidgetSpace::World);
	Widget->SetDrawAtDesiredSize(true);
	Widget->SetPivot(FVector2D(0.5f, 0.5f));
	Widget->SetCollisionEnabled(ECollisionEnabled::NoCollision);
	Widget->SetRelativeScale3D(FVector(1.f / PixelsPerCm));
}

void AWorldText::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);
	Refresh(); // visible in the editor viewport
}

void AWorldText::BeginPlay()
{
	Super::BeginPlay();
	Refresh(); // the Slate widget is not copied into the PIE world
}

void AWorldText::Refresh()
{
	// Slate font size is in points; cap height comes out close to Size cm after the scale above
	Widget->SetSlateWidget(SNew(STextBlock)
		.Text(Text)
		.Justification(ETextJustify::Center)
		.ColorAndOpacity(FSlateColor(Color))
		.Font(FCoreStyle::GetDefaultFontStyle("Bold", FMath::RoundToInt(Size * PixelsPerCm))));
}
